import json
import os
from itertools import islice
from json import JSONDecodeError
from pathlib import Path

import click
from jinja2 import FileSystemLoader, Environment
from ollama import Client

from ._base import search_judge
from ._utils import load_df

SYSTEM_PROMPT_TEMPLATE_NAME = "_llm_system_prompt.j2"


def _new_connection(host, port):
    return Client(f"{host}:{port}")


def _load_system_prompt_template():
    loader = FileSystemLoader(Path(__file__).parent)
    env = Environment(loader=loader)
    tpl = env.get_template(SYSTEM_PROMPT_TEMPLATE_NAME)
    return tpl


def _generate(client, rule_config, model, title_abs):
    tpl = _load_system_prompt_template()
    system_prompt = tpl.render(**rule_config)
    response = client.generate(model=model, prompt=title_abs, system=system_prompt)
    return response.response


@search_judge.command()
@click.argument(
    "search_results",
    required=True,
    type=click.Path(exists=True, dir_okay=False, file_okay=True, readable=True),
)
@click.option(
    "-c", "--config-file",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, readable=True),
    required=True,
    help="path to a JSON configuration containing inclusion and exclusion criteria",
)
@click.option(
    "-m", "--model",
    type=click.Choice(["llama3.1", "command-r7b", "gemma3n", "deepseek-r1:14b"]),
    default="llama3.1",
    help="the name of the large language model to use",
    show_default=True,
)
@click.option(
    "--ollama-host",
    type=click.STRING,
    default="localhost",
    help="host running Ollama",
    show_default=True,
)
@click.option(
    "--ollama-port",
    type=click.IntRange(1024, 65535, clamp=True),
    default=11434,
    help="port on which Ollama is listening",
    show_default=True,
)
@click.option(
    "--limit",
    type=click.INT,
    default=None,
    help="maximum number of results to process",
    required=False,
)
def llm(search_results, config_file, model, ollama_host, ollama_port, limit):
    """Use a large language model to filter out irrelevant search results."""
    DEFAULT_EXCLUDED_ATTRIBUTES = {"cluster_id", "include", "exclude_reason"}
    search_results_path = Path(search_results)
    results_df = load_df(search_results_path)
    with open(config_file, "r") as f:
        rule_config = json.load(f)
    ollama_client = _new_connection(ollama_host, ollama_port)

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
                if key not in DEFAULT_EXCLUDED_ATTRIBUTES
            )
            answered = False
            answer_obj = {}
            while not answered and (answer := _generate(ollama_client, rule_config, model, row_str)):
                try:
                    answer_obj = json.loads(answer)
                    answered = True
                except JSONDecodeError as err:
                    click.echo(err, err=True)
            status = answer_obj["answer"]
            results_df.at[ix, "include"] = status

            if status == "exclude":
                results_df.at[ix, "exclude_reason"] = answer_obj["justification"]
            elif status == "include":
                results_df.at[ix, "exclude_reason"] = ""

    output_path = search_results_path.parent / f"{search_results_path.stem}-llm.xlsx"
    results_df.to_excel(output_path, index=False)
    click.echo(f"saved results to {click.style(output_path, bold=True)}", color=True, err=False)
