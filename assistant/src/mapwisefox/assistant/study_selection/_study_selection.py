import logging
import os
import sys
from functools import partial
from itertools import islice
from pathlib import Path

import click

from mapwisefox.assistant.config import ConfigValidationError, load_selection_config
from mapwisefox.assistant.config._schemas import SelectionResponse
from mapwisefox.assistant.tools import load_df, load_template
from mapwisefox.assistant.tools.callbacks import (
    make_stderr_callback,
    make_thinking_callback,
    write_stdout,
)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__file__)


SYSTEM_PROMPT_TEMPLATE = Path(__file__).parent / f"{Path(__file__).stem}.j2"
DEFAULT_EXCLUDED_ATTRIBUTES = ["cluster_id", "include", "exclude_reason"]


@click.command("study-selection")
@click.argument(
    "search_results",
    required=True,
    type=click.Path(exists=True, dir_okay=False, file_okay=True, readable=True),
)
@click.option(
    "-c",
    "--config-file",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, readable=True),
    required=True,
    envvar="MWF_ASSISTANT_SELECTION_CONFIG",
    help="path to a JSON configuration containing the study objective and "
    "inclusion/exclusion criteria (see assistant/schemas/study-selection.schema.json)",
)
@click.option(
    "--limit",
    type=click.INT,
    default=None,
    help="maximum number of results to process",
    required=False,
)
@click.option(
    "-i",
    "--ignore-attributes",
    type=click.STRING,
    multiple=True,
    help="ignore these attributes from the processing of individual selection records",
    default=DEFAULT_EXCLUDED_ATTRIBUTES,
    show_default=True,
)
@click.pass_context
def study_selection(ctx, search_results, config_file, limit, ignore_attributes):
    """Use an LLM to select primary studies according to criteria.

    A file containing a table of primary studies containing at least the title,
    keywords and abstract of each study is provided as input. Then, the LLM
    decides based whether each record meets a set of criteria (which are also
    provided by the user).
    """
    ignored_attrs = set(
        ignore_attributes if len(ignore_attributes) > 0 else DEFAULT_EXCLUDED_ATTRIBUTES
    )
    search_results_path = Path(search_results)
    results_df = load_df(search_results_path)

    try:
        rule_config = load_selection_config(config_file)
    except ConfigValidationError as err:
        raise click.UsageError(str(err))

    provider = ctx.obj.provider_factory(
        on_error=make_stderr_callback(log),
        on_thinking=make_thinking_callback(),
        on_text=write_stdout,
    )
    if not provider.ensure_model():
        exit(1)

    json_generator = provider.new_json_generator()
    expected_json_schema = SelectionResponse.model_json_schema()
    generate_json = partial(
        json_generator.generate_json,
        system_prompt_template=load_template(SYSTEM_PROMPT_TEMPLATE),
        template_data=rule_config.model_dump(),
        response_schema=expected_json_schema,
    )

    count = len(results_df) if limit is None else limit
    items = islice(results_df.iterrows(), 0, count)

    with click.progressbar(
        items,
        length=count,
        label="processing search results",
        fill_char=click.style("#", fg="green"),
        empty_char=click.style("-", fg="white", dim=True),
    ) as df_rows:
        for ix, row in df_rows:
            row_str = os.linesep.join(
                f"{key}: {value}"
                for key, value in row.items()
                if key not in ignored_attrs
            )
            answer_obj = generate_json(row_str)
            status = answer_obj["answer"]
            results_df.at[ix, "include"] = status

            if status == "exclude":
                results_df.at[ix, "exclude_reason"] = answer_obj["justification"]
            elif status == "include":
                results_df.at[ix, "exclude_reason"] = ""

    model_stem = ctx.obj.model_choice.replace(":", "_")
    output_path = (
        search_results_path.parent / f"{search_results_path.stem}-{model_stem}.xlsx"
    )
    results_df.to_excel(output_path, index=False)
    click.echo(
        f"saved results to {click.style(output_path, bold=True)}", color=True, err=False
    )
