import io
import logging
import os
from collections import defaultdict

import pandas as pd
import urllib3
from functools import partial
from typing import Callable, Any

from pathlib import Path

import click
from requests.exceptions import HTTPError

from mapwisefox.assistant.config import (
    ConfigValidationError,
    ReaderType,
    load_qa_config,
)
from mapwisefox.assistant.instrumentation import timer
from mapwisefox.assistant.tools import (
    load_df,
    load_template,
    FileProvider,
)
from mapwisefox.assistant.tools.callbacks import (
    make_stderr_callback,
    make_thinking_callback,
    write_stdout,
)
from mapwisefox.assistant.tools.extras import try_import
from mapwisefox.assistant.tools.logging import get_logger
from mapwisefox.assistant.tools.pdf import (
    FileContentsExtractor,
    CachingFileContentsExtractor,
    FileContentsExtractionError,
    ExtractionFailureReason,
)

_COMMAND_NAME = "study-qa"
log = get_logger(_COMMAND_NAME)
urllib3.disable_warnings()


def _extract_context(cfg: dict, crit: dict) -> dict:
    return {
        "topic": cfg["topic"],
        "question": crit["question"],
        "description": crit["description"],
        "scoring": crit["scoring"],
    }


def get_default_pdf_reader(dpi: int, layout_model: str) -> FileContentsExtractor:
    pdf = try_import("mapwisefox.assistant.tools.pdf._pdf")
    return pdf.BasicPdfMarkdownExtractor(dpi=dpi, layout_model=layout_model)


def reader_factory(
    reader_type: ReaderType,
    layout_model: str,
    dpi: int = 150,
    timeout_seconds: float = 30.0,
) -> FileContentsExtractor:
    if reader_type == ReaderType.docling:
        docling = try_import("mapwisefox.assistant.tools.pdf._docling")
        return docling.DoclingExtractor(
            error_callback=log.warning, timeout_seconds=timeout_seconds
        )

    return get_default_pdf_reader(dpi, layout_model)


@timer(callback=log.info, label="read-pdf")
def _extract_file_contents(extractor: FileContentsExtractor, local_path: Path) -> str:
    caching_reader = CachingFileContentsExtractor(local_path.parent, extractor)
    return caching_reader.read_file(local_path)


def _read_paper(
    paper_id: Any,
    local_file_path: Path,
    pdf_reader: FileContentsExtractor,
    max_retries: int,
    get_failsafe_reader: Callable,
):
    retries, local_reader = max_retries, pdf_reader
    while retries >= 0:
        try:
            return True, _extract_file_contents(local_reader, local_file_path)
        except FileContentsExtractionError as exc:
            if exc.reason not in {
                ExtractionFailureReason.Timeout,
                ExtractionFailureReason.BackendError,
            }:
                log.error(
                    "unhandled error while extracting contents of paper %r", paper_id
                )
                break  # return False, None

            log.warning(
                "failed to extract contents of paper %r, defaulting to failsafe reader",
                paper_id,
            )
            local_reader = get_failsafe_reader()
            retries -= 1

    # maximum retries exceeded
    return False, None


@timer(log.info, "read-pdf-files")
def _extract_pdf_contents(
    df: pd.DataFrame,
    url_column: str,
    file_provider: FileProvider,
    pdf_reader: FileContentsExtractor,
    default_pdf_reader_factory: Callable[[], FileContentsExtractor],
    max_retries: int = 3,
):
    user_prompts = dict()
    failed = []
    for idx, paper_metadata in df.iterrows():
        download_url = paper_metadata[url_column]
        try:
            local_file_path = file_provider(download_url)

            read_ok, contents = _read_paper(
                idx,
                local_file_path,
                pdf_reader,
                max_retries,
                default_pdf_reader_factory,
            )
            if read_ok:
                user_prompts[(idx, download_url, local_file_path)] = contents
            else:
                failed.append((idx, download_url))
        except (AttributeError, ValueError, HTTPError) as e:
            failed.append((idx, download_url))
            log.warning("failed to download %s: %s", download_url, e)

    return user_prompts, failed


DEFAULT_MAX_SCORE_RETRIES = 3


def _score_criterion(
    eval_c: Callable[..., dict],
    template_data: dict,
    user_prompt: str,
    label: str,
    max_retries: int,
) -> dict:
    for _ in range(max_retries + 1):
        obj = eval_c(template_data=template_data, user_prompt=user_prompt)
        log.debug("LLM answer: %s", obj)
        if obj.get("score"):
            return obj

    log.warning("criterion %r left unscored after %d attempts", label, max_retries + 1)
    return {"score": None, "reason": "left unscored: LLM did not return a usable score"}


@timer(callback=log.info, label="paper-evaluation")
def _evaluate_paper(
    user_prompt: str,
    local_path: Path,
    generate_json: Callable[[dict, str], dict],
    qa_config: dict,
    qa_criteria: dict,
    max_score_retries: int = DEFAULT_MAX_SCORE_RETRIES,
) -> dict | None:
    try:
        result = {}

        for c in qa_criteria:
            key = c["label"]
            ctx = _extract_context(qa_config, c)

            c_timer = timer(log.info, f"{local_path.stem}: generate-json({key})")
            eval_c = c_timer(generate_json)
            result[key] = _score_criterion(
                eval_c, ctx, user_prompt, key, max_score_retries
            )

        return result
    except Exception as e:
        styled_url = click.style(local_path, italic=True, underline=True)
        click.echo(f"Failed to evaluate paper {styled_url}. Error: {e}", err=True)
        return None


@timer(log.info, "evaluation")
def _evaluate_papers(
    paper_contents: dict[Any, Any], generate_json: partial[Any], qa_config, qa_criteria
) -> dict[Any, Any]:
    results = {}
    for (idx, download_url, local_file_path), user_prompt in paper_contents.items():
        result = _evaluate_paper(
            user_prompt,
            local_file_path,
            generate_json,
            qa_config,
            qa_criteria,
        )
        if result is None:
            log.warning("unable to process item %d: %r", idx, download_url)
            continue
        results[idx] = result
    return results


def _fill_results(df: pd.DataFrame, qa_criteria: dict, results: dict) -> pd.DataFrame:
    criteria_dict = {c["label"]: c for c in qa_criteria}

    for idx, result in results.items():
        evaluation = defaultdict(list)
        for i, label in enumerate(result, 1):
            score = result[label].pop("score", 0)
            df.loc[idx, label] = score
            evaluation[criteria_dict[label]["category"]].append(
                os.linesep.join(
                    [
                        f"{i}. **{criteria_dict[label]["question"]}**",
                        *result[label].values(),
                    ]
                )
            )
        evaluation_text = io.StringIO()
        for category, answers in evaluation.items():
            evaluation_text.write(f"{os.linesep}# {category}{2 * os.linesep}")
            evaluation_text.write(f"{2 * os.linesep}".join(answers))
            evaluation_text.write(os.linesep)

        df.loc[idx, "evaluation"] = evaluation_text.getvalue()

    return df


@click.command(
    _COMMAND_NAME,
    help=r"""Use an LLM to assess the quality of primary studies against criteria.

    FILE is an Excel spreadsheet with a column containing an URL (https:// or
    file:// supported) to each primary study's PDF. For each study, its text
    is extracted from the PDF, and every criterion is scored independently by
    the LLM. Criteria that can't be scored after repeated attempts are left
    empty, so downstream tooling can treat them as unscored.""",
)
@click.argument(
    "file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.option(
    "-u",
    "--url-column",
    type=click.STRING,
    default="url",
    show_default=True,
    help="column in the Excel sheet which contains URLs to primary studies",
)
@click.option(
    "--index-column",
    "index_col",
    type=click.STRING,
    required=False,
    default=None,
    help="column in the source Excel sheet containing row identifier",
)
@click.option(
    "-c",
    "--config",
    "qa_config_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    envvar="MWF_ASSISTANT_QA_CONFIG",
    help=r"""path to a JSON configuration containing the QA topic and scoring
    criteria (see common-config/schemas/study-qa.schema.json)""",
)
@click.option(
    "-e",
    "--reader-type",
    "reader_type",
    type=click.Choice(choices=list(ReaderType)),
    default=ReaderType.custom,
    show_default=True,
    help="the type of engine to use for reading documents",
)
@click.option(
    "-l",
    "--layout-model",
    "layout_config_path",
    type=click.STRING,
    required=True,
    default="lp://PubLayNet/tf_efficientdet_d0/config",
    show_default=True,
    help="model used to infer the layout of a PDF file; see LayoutParser for values.",
)
@click.option(
    "--insecure-skip-tls-verify",
    is_flag=True,
    default=False,
    help="disable TLS certificate verification when downloading primary study PDFs",
)
@click.option(
    "-D",
    "--download-dir",
    "download_dir",
    default=Path.cwd() / "downloads",
    help="download directory where papers will be stored.",
    show_default=True,
)
@click.pass_context
def study_qa(
    ctx,
    file: Path,
    index_col: str,
    url_column: str,
    qa_config_path: Path,
    layout_config_path: str,
    reader_type: ReaderType,
    insecure_skip_tls_verify: bool,
    download_dir: Path,
):
    try:
        qa_config = load_qa_config(qa_config_path).model_dump()
    except ConfigValidationError as err:
        raise click.UsageError(str(err))
    qa_criteria = qa_config["criteria"]

    download_dir = Path(download_dir).resolve()
    file = Path(file).resolve()
    file_provider = FileProvider(
        download_dir, verify_tls=not insecure_skip_tls_verify
    )
    pdf_reader = reader_factory(reader_type, layout_config_path)

    df = load_df(file, index_col=index_col)
    for c in qa_criteria:
        column = c["label"]
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").astype("Float64")
        else:
            df[column] = pd.Series(dtype="Float64", index=df.index)
    expected_json_schema = {
        "title": "evaluation",
        "description": "primary study evaluation",
        "type": "object",
        "properties": {"score": {"type": "number"}, "reason": {"type": "string"}},
        "additionalProperties": False,
        "strict": True,
        "required": ["score", "reason"],
    }
    provider = ctx.obj.provider_factory(
        on_error=make_stderr_callback(log),
        on_thinking=make_thinking_callback(),
        on_text=write_stdout,
    )
    if not provider.ensure_model():
        exit(1)

    json_generator = provider.new_json_generator()
    generate_json = partial(
        json_generator.generate_json,
        system_prompt_template=load_template(
            Path(__file__).parent / f"{Path(__file__).stem}.j2"
        ),
        response_schema=expected_json_schema,
    )

    default_reader = partial(
        get_default_pdf_reader, dpi=150, layout_model=layout_config_path
    )
    markdown_texts, failed = _extract_pdf_contents(
        df, url_column, file_provider, pdf_reader, default_reader, 1
    )
    if failed:
        log.warning("failed to download %d files", len(failed))
        for f in failed:
            log.warning(f)
    results = _evaluate_papers(markdown_texts, generate_json, qa_config, qa_criteria)
    df = _fill_results(df, qa_criteria, results)
    output_path = file.parent / f"{file.stem}-{ctx.obj.model_choice}{file.suffix}"
    df.to_excel(output_path, index=False if index_col is None else True)
