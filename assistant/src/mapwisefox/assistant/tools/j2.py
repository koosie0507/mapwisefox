from pathlib import Path
from jinja2 import FileSystemLoader, Environment, Template


def load_template(file: Path) -> Template:
    file = Path(file)
    loader = FileSystemLoader(file.parent)
    env = Environment(loader=loader)
    tpl = env.get_template(file.name)
    return tpl
