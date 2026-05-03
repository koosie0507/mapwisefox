import click


@click.group()
@click.pass_context
def search_judge(ctx):
    """Commands for judging the results of a search from various perspectives."""
