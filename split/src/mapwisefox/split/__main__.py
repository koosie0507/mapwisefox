import click

from ._simple import simple
from ._assignment import n_by_k_evals


@click.group()
def split():
    pass


split.add_command(simple)
split.add_command(n_by_k_evals)


if __name__ == "__main__":
    split()
