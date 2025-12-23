import click

from ._simple import simple


@click.group()
def split():
    pass


if __name__ == "__main__":
    split.add_command(simple)
    split()
