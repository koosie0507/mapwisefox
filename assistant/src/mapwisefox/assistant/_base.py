from functools import partial

import click

from mapwisefox.assistant.config import AssistantParams, ProviderChoice
from mapwisefox.assistant.config._validate import validate_config
from mapwisefox.assistant.quality_assessment import cli as study_qa
from mapwisefox.assistant.study_selection import cli as study_selection
from mapwisefox.assistant.tools.llm import (
    OllamaProvider,
    OpenAIProvider,
    AnthropicProvider,
    GoogleProvider,
    BedrockProvider,
)


def _ollama_provider(model_choice: str, ollama_endpoint: str, api_key: str):
    return partial(
        OllamaProvider, model=model_choice, ollama_host=ollama_endpoint, api_key=api_key
    )


def _openai_provider(model_choice: str, api_key: str):
    return partial(OpenAIProvider, model=model_choice, api_key=api_key)


def _anthropic_provider(model_choice: str, api_key: str):
    return partial(AnthropicProvider, model=model_choice, api_key=api_key)


def _google_provider(model_choice: str, api_key: str):
    return partial(GoogleProvider, model=model_choice, api_key=api_key)


def _bedrock_provider(model_choice: str, api_key: str):
    return partial(BedrockProvider, model=model_choice, api_key=api_key)


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


@click.group(
    help=r"""Use an LLM to help with systematic literature review tasks.

-m/--model, -p/--provider, and the provider-specific options below are shared by
all assistant subcommands."""
)
@click.option(
    "-m",
    "--model",
    type=click.STRING,
    default="gpt-oss:20b",
    help="the name of the large language model to use",
    show_default=True,
)
@click.option(
    "-p",
    "--provider",
    type=click.Choice(ProviderChoice),
    default=ProviderChoice.ollama,
    help="the LLM provider used by study-selection and study-qa",
    show_default=True,
)
@click.option(
    "--ollama-endpoint",
    type=click.STRING,
    default="http://localhost:11434",
    help="address where Ollama is listening",
    show_default=True,
)
@click.option(
    "--api-key",
    type=click.UNPROCESSED,
    callback=_validate_api_key,
    envvar="MWF_ASSISTANT_API_KEY",
    help="API key used to connect to LLM provider APIs (OpenAI, Google, Anthropic, ...)",
    default="",
)
@click.pass_context
def assistant(ctx, model, provider, ollama_endpoint, api_key):
    obj = ctx.ensure_object(AssistantParams)
    obj.model_choice = model
    obj.ollama_endpoint = ollama_endpoint
    obj.api_key = api_key

    match provider:
        case ProviderChoice.openai:
            obj.provider_factory = _openai_provider(model, api_key)
        case ProviderChoice.anthropic:
            obj.provider_factory = _anthropic_provider(model, api_key)
        case ProviderChoice.google:
            obj.provider_factory = _google_provider(model, api_key)
        case ProviderChoice.bedrock:
            obj.provider_factory = _bedrock_provider(model, api_key)
        case _:
            obj.provider_factory = _ollama_provider(model, ollama_endpoint, api_key)


assistant.add_command(study_selection)
assistant.add_command(study_qa)
assistant.add_command(validate_config)
