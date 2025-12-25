import importlib
from ._base import assistant


def main():
    importlib.import_module("mapwisefox.assistant._llm", None)
    assistant()


if __name__ == "__main__":
    main()
