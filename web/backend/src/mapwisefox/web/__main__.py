import click
import uvicorn

from mapwisefox.web._fast_api import _init_app


@click.command()
@click.option("--host", "-H", type=click.STRING, default="0.0.0.0")
@click.option("--port", "-P", type=click.INT, default=8000)
def main(host, port):
    app = _init_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
