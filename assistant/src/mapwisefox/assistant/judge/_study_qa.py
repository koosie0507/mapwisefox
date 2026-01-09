import io
import json
import logging
import os
import sys
from collections import defaultdict
from multiprocessing import Process, Pipe, Lock as create_lock
from multiprocessing.connection import Connection

import pandas as pd
import urllib3
from functools import partial
from typing import Callable, Any

from pathlib import Path

import click

from mapwisefox.assistant.config import ReaderType
from mapwisefox.assistant.instrumentation import timer
from mapwisefox.assistant.tools import (
    load_df,
    load_template,
    FileProvider,
)
from mapwisefox.assistant.tools.extras import try_import
from mapwisefox.assistant.tools.pdf import (
    FileContentsExtractor,
    CachingFileContentsExtractor,
)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__file__)

urllib3.disable_warnings()


def _extract_context(cfg: dict, crit: dict) -> dict:
    return {
        "topic": cfg["topic"],
        "question": crit["question"],
        "description": crit["description"],
        "scoring": crit["scoring"],
    }


def _write_thoughts():
    wrote_label = False

    def _(msg: str):
        nonlocal wrote_label
        if not wrote_label:
            click.secho("Thinking ... ", nl=True, color=True, fg="blue", italic=True)
        click.secho(msg, nl=False, color=True, fg="blue", italic=True)
        wrote_label = True

    return _


def _write_stdout(msg: str, *args):
    output_text = msg % args if len(args) > 0 else msg
    click.echo(output_text, nl=False)


def _write_stderr(msg: str, e: Exception):
    log.error(msg, exc_info=e)


def get_default_pdf_reader(dpi: int, layout_model: str) -> FileContentsExtractor:
    pdf = try_import("mapwisefox.assistant.tools.pdf._pdf")
    return pdf.BasicPdfMarkdownExtractor(dpi=dpi, layout_model=layout_model)


def reader_factory(
    reader_type: ReaderType, layout_model: str, dpi: int = 150
) -> FileContentsExtractor:
    if reader_type == ReaderType.docling:
        docling = try_import("mapwisefox.assistant.tools.pdf._docling")
        return docling.DoclingExtractor(error_callback=log.warning)

    return get_default_pdf_reader(dpi, layout_model)


@timer(callback=log.info, label="read-pdf")
def _read_markdown(
    conn: Connection, extractor: FileContentsExtractor, local_path: Path
) -> None:
    try:
        caching_reader = CachingFileContentsExtractor(local_path.parent, extractor)
        markdown = caching_reader.read_file(local_path)
        conn.send(markdown)
        exit(0)
    except Exception:
        conn.send("")
        exit(1)
    finally:
        conn.close()


@timer(log.info, "read-pdf-files")
def _extract_pdf_contents(
    df: pd.DataFrame,
    url_column: str,
    file_provider: FileProvider,
    pdf_reader: FileContentsExtractor,
    default_pdf_reader_factory: Callable[[], FileContentsExtractor],
    max_retries: int = 3,
    document_timeout_seconds: float = 60.0,
):
    user_prompts = dict()
    lock = create_lock()
    failed = []
    for idx, paper_metadata in df.iterrows():
        download_url = paper_metadata[url_column]
        read, retries, local_reader = False, max_retries, pdf_reader
        while not read and retries >= 0:
            try:
                lock.acquire()
                local_file_path = file_provider(download_url)
                recv_conn, send_conn = Pipe()
                process = Process(
                    target=_read_markdown,
                    args=(send_conn, local_reader, local_file_path),
                )
                process.start()

                # wait up to document_timeout_seconds to finish reading the PDF
                timed_out = True
                if recv_conn.poll(timeout=document_timeout_seconds):
                    markdown = recv_conn.recv()
                    timed_out = False
                else:
                    markdown = "timeout"
                    process.terminate()

                process.join()
                if timed_out:
                    raise TimeoutError(document_timeout_seconds)
                if process.exitcode != 0:
                    raise Exception(markdown)

                user_prompts[(idx, download_url, local_file_path)] = markdown
                read = True
            except Exception as e:
                log.error(
                    "couldn't process paper %r using %r: %r. reverting to failsafe reader",
                    idx,
                    str(type(pdf_reader).__name__),
                    str(e)[:50],
                )
                local_reader = default_pdf_reader_factory()
                retries -= 1
            finally:
                lock.release()

        if not read:
            failed.append((idx, download_url))

    return user_prompts, failed


@timer(callback=log.info, label="paper-evaluation")
def _evaluate_paper(
    user_prompt: str,
    local_path: Path,
    generate_json: Callable[[dict, str], dict],
    qa_config: dict,
    qa_criteria: dict,
) -> dict | None:
    try:
        result = {}

        for c in qa_criteria:
            key = c["label"]
            ctx = _extract_context(qa_config, c)

            c_timer = timer(log.info, f"{local_path.stem}: generate-json({key})")
            eval_c = c_timer(generate_json)
            obj = None
            while obj is None or not obj.get("score"):
                obj = eval_c(template_data=ctx, user_prompt=user_prompt)
                log.debug("LLM answer: %s", obj)
            result[key] = obj

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


@click.command("study-qa")
@click.argument(
    "file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.option(
    "-u",
    "--url-column",
    type=click.STRING,
    default="url",
    help="column in the Excel sheet which contains URLs to primary studies",
)
@click.option(
    "-k",
    "--key",
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
    help="path to QA rule config file",
)
@click.option(
    "-e",
    "--reader-type",
    "reader_type",
    type=click.Choice(choices=list(ReaderType)),
    default=ReaderType.custom,
    help="the type of engine to use for reading documents",
)
@click.option(
    "-l",
    "--layout-model",
    "layout_config_path",
    type=click.STRING,
    required=True,
    default="lp://PubLayNet/tf_efficientdet_d0/config",
    help="model used to infer the layout of a PDF file; see LayoutParser for values.",
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
):
    file = Path(file).resolve()
    file_provider = FileProvider(file.parent / "downloads")
    with open(qa_config_path, "r") as jfp:
        qa_config = json.load(jfp)
    qa_criteria = qa_config["criteria"]
    pdf_reader = reader_factory(reader_type, layout_config_path)

    df = load_df(file, index_col=index_col)
    for c in qa_criteria:
        df[c["label"]] = df[c["label"]].astype("Float64")
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
        on_error=_write_stderr, on_thinking=_write_thoughts(), on_text=_write_stdout
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
        df, url_column, file_provider, pdf_reader, default_reader, 1, 30
    )
    results = _evaluate_papers(markdown_texts, generate_json, qa_config, qa_criteria)
    df = _fill_results(df, qa_criteria, results)
    output_path = file.parent / f"{file.stem}-{ctx.obj.model_choice}{file.suffix}"
    df.to_excel(output_path, index=False)
