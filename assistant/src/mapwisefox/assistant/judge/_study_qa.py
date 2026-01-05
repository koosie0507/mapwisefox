import io
import json
import logging
import os
import sys
from collections import defaultdict

import urllib3
from functools import partial
from typing import Callable

from pathlib import Path

import click


from mapwisefox.assistant.instrumentation import timer
from mapwisefox.assistant.tools import (
    load_df,
    load_template,
    FileProvider,
)
from mapwisefox.assistant.tools.pdf import (
    PdfMarkdownFileExtractor,
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


@timer(callback=log.info, label="read-pdf")
def _read_text(layout_model: str, local_path: Path, dpi: int = 150) -> str:
    extractor = PdfMarkdownFileExtractor(dpi, layout_model=layout_model)
    return extractor.read_file(local_path)


@timer(callback=log.info, label="evaluate-paper")
def _evaluate_paper(
    layout_model: str,
    local_path: Path,
    generate_json: Callable[[dict, str], dict],
    qa_config: dict,
    qa_criteria: dict,
    **kwargs,
) -> dict | None:
    try:
        user_prompt = _read_text(layout_model, local_path, kwargs.pop("dpi", 150))
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
    "-c",
    "--config",
    "qa_config_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
    help="path to QA rule config file",
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
    ctx, file: Path, url_column: str, qa_config_path: Path, layout_config_path: str
):
    file = Path(file).resolve()
    file_provider = FileProvider(file.parent / "downloads")
    with open(qa_config_path, "r") as jfp:
        qa_config = json.load(jfp)
    qa_criteria = qa_config["criteria"]

    df = load_df(file)
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

    results = {}
    for idx, paper_metadata in df.iterrows():
        download_url = paper_metadata[url_column]
        local_file_path = file_provider(download_url)
        result = _evaluate_paper(
            layout_config_path,
            local_file_path,
            generate_json,
            qa_config,
            qa_criteria,
        )
        if result is None:
            log.warning("unable to process item %d: %r", idx, download_url)
            continue
        results[idx] = result

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
            evaluation_text.write(f"{os.linesep}# {category}{2*os.linesep}")
            evaluation_text.write(f"{2*os.linesep}".join(answers))
            evaluation_text.write(os.linesep)

        df.loc[idx, "evaluation"] = evaluation_text.getvalue()

    output_path = file.parent / f"{file.stem}-{ctx.obj.model_choice}{file.suffix}"
    df.to_excel(output_path, index=False)
