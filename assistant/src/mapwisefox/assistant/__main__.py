import importlib
from ._base import assistant


def main():
    importlib.import_module("mapwisefox.assistant.study_selection", None)
    importlib.import_module("mapwisefox.assistant.judge", None)
    assistant()


if __name__ == "__main__":
    main()
