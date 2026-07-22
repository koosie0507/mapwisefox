import json
from pathlib import Path

from mapwisefox.assistant.config._schema_export import SCHEMA_FILES, write_schema_files

PUBLISHED_SCHEMAS_DIR = Path(__file__).parents[4] / "schemas"


def test_write_schema_files_creates_one_file_per_schema(tmp_path):
    write_schema_files(tmp_path)

    for filename in SCHEMA_FILES:
        assert (tmp_path / filename).exists()


def test_write_schema_files_content_matches_model_json_schema(tmp_path):
    write_schema_files(tmp_path)

    for filename, model in SCHEMA_FILES.items():
        written = json.loads((tmp_path / filename).read_text())
        assert written == model.model_json_schema()


def test_published_schemas_are_up_to_date(tmp_path):
    """Guards against editing a pydantic config model without regenerating
    the checked-in JSON Schema files under assistant/schemas/."""
    write_schema_files(tmp_path)

    for filename in SCHEMA_FILES:
        published = (PUBLISHED_SCHEMAS_DIR / filename).read_text()
        regenerated = (tmp_path / filename).read_text()
        assert published == regenerated, (
            f"{filename} is stale; run the schema-export script to regenerate "
            f"assistant/schemas/{filename}"
        )
