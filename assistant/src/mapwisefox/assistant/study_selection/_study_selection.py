import json
import os
from functools import partial
from itertools import islice
from pathlib import Path

import click

from mapwisefox.assistant.tools import load_df, OllamaProvider, load_template


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
    help="path to a JSON configuration containing inclusion and exclusion criteria",
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
    with open(config_file, "r") as f:
        rule_config = json.load(f)
    provider = OllamaProvider(
        ctx.obj.model_choice, f"{ctx.obj.ollama_host}:{ctx.obj.ollama_port}"
    )
    json_generator = provider.new_json_generator()
    generate_json = partial(
        json_generator.generate_json,
        system_prompt_template=load_template(SYSTEM_PROMPT_TEMPLATE),
        template_data=rule_config,
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
