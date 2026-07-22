import json
from pathlib import Path

from mapwisefox.assistant.config._schemas import QAConfig, SelectionConfig


SCHEMA_FILES = {
    "study-selection.schema.json": SelectionConfig,
    "study-qa.schema.json": QAConfig,
}


def write_schema_files(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, model in SCHEMA_FILES.items():
        schema_json = json.dumps(model.model_json_schema(), indent=2)
        (output_dir / filename).write_text(schema_json + "\n")


if __name__ == "__main__":
    write_schema_files(Path(__file__).parents[4] / "schemas")
