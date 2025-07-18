import importlib
from ._base import search_judge


def main():
    importlib.import_module("mapwisefox.search_judge._quality", None)
    importlib.import_module("mapwisefox.search_judge._llm", None)
    search_judge()


if __name__ == "__main__":
    main()
