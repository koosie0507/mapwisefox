import click
import mapwisefox.metrics._kappa_score as ks


@click.group("metrics")
def metrics():
    pass


metrics.add_command(ks.main, "kappa-score")
