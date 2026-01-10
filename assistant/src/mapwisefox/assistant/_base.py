from functools import partial

import click

from mapwisefox.assistant.config import AssistantParams, ModelChoice, ProviderChoice
from mapwisefox.assistant.judge._study_qa import study_qa
from mapwisefox.assistant.study_selection._study_selection import study_selection
from mapwisefox.assistant.tools.llm import (
    OllamaProvider,
    OpenAIProvider,
    AnthropicProvider,
    GoogleProvider,
)


def _ollama_provider(model_choice: str, ollama_host: str, ollama_port: int):
    return partial(
        OllamaProvider, model=model_choice, ollama_host=f"{ollama_host}:{ollama_port}"
    )


def _openai_provider(model_choice: str, api_key: str):
    return partial(OpenAIProvider, model=model_choice, api_key=api_key)


def _anthropic_provider(model_choice: str, api_key: str):
    return partial(AnthropicProvider, model=model_choice, api_key=api_key)


def _google_provider(model_choice: str, api_key: str):
    return partial(GoogleProvider, model=model_choice, api_key=api_key)


def _validate_api_key(ctx, param, value):
    if param.name != "api_key" or ctx.params["provider"] not in {
        ProviderChoice.openai,
        ProviderChoice.anthropic,
    }:
        return value
    if value is None or len(val_str := str(value).strip()) < 1:
        raise click.BadParameter(
            f"expected user to supply an API key when using {ctx.params["provider"]}"
        )
    return val_str


@click.group()
@click.option(
    "-m",
    "--model",
    type=click.Choice(ModelChoice),
    default=ModelChoice.gpt_oss,
    help="the name of the large language model to use",
    show_default=True,
)
@click.option(
    "-p",
    "--provider",
    type=click.Choice(ProviderChoice),
    default=ProviderChoice.ollama,
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
    "-k",
    "--api-key",
    type=click.UNPROCESSED,
    callback=_validate_api_key,
    envvar="MWF_ASSISTANT_API_KEY",
    help="API key used to connect to LLM provider APIs (OpenAI, Google, Anthropic, ...)",
    default="",
)
@click.pass_context
def assistant(ctx, model, provider, ollama_host, ollama_port, api_key):
    """Spawns an LLM assistant to help with systematic literature reviews."""
    obj = ctx.ensure_object(AssistantParams)
    obj.model_choice = ModelChoice(model)
    obj.ollama_host = ollama_host
    obj.ollama_port = int(ollama_port)
    obj.api_key = api_key

    match provider:
        case ProviderChoice.openai:
            obj.provider_factory = _openai_provider(model, api_key)
        case ProviderChoice.anthropic:
            obj.provider_factory = _anthropic_provider(model, api_key)
        case ProviderChoice.google:
            obj.provider_factory = _google_provider(model, api_key)
        case _:
            obj.provider_factory = _ollama_provider(model, ollama_host, ollama_port)


assistant.add_command(study_selection)
assistant.add_command(study_qa)
