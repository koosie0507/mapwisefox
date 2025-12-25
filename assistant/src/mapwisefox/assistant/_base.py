import click


@click.group()
@click.pass_context
def assistant(ctx):
    """Spawns an LLM assistant to help with systematic literature reviews."""
