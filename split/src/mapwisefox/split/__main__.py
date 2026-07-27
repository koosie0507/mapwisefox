"""Expose the Split workload command group."""

import click

from ._assignment import n_by_k_evals
from ._simple import simple


@click.group(help="Divide Excel study workbooks among reviewers.")
def split() -> None:
    """Divide Excel study workbooks among reviewers."""


split.add_command(simple)
split.add_command(n_by_k_evals)


if __name__ == "__main__":
    split()
