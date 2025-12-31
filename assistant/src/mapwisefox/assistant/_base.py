import click

from mapwisefox.assistant.config import AssistantParams, ModelChoice
from mapwisefox.assistant.judge._study_qa import study_qa
from mapwisefox.assistant.study_selection._study_selection import study_selection


@click.group()
@click.option(
    "-m",
    "--model",
    type=click.Choice(ModelChoice),
    default=ModelChoice.gpt,
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
@click.pass_context
def assistant(ctx, model, ollama_host, ollama_port):
    """Spawns an LLM assistant to help with systematic literature reviews."""
    obj = ctx.ensure_object(AssistantParams)
    obj.model_choice = ModelChoice(model)
    obj.ollama_host = ollama_host
    obj.ollama_port = int(ollama_port)


assistant.add_command(study_selection)
assistant.add_command(study_qa)
