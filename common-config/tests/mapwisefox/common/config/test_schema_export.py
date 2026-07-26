import json
import runpy
from pathlib import Path

from mapwisefox.common.config._schema_export import SCHEMA_FILES, write_schema_files

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
    the checked-in JSON Schema files under common-config/schemas/."""
    write_schema_files(tmp_path)

    for filename in SCHEMA_FILES:
        published = (PUBLISHED_SCHEMAS_DIR / filename).read_text()
        regenerated = (tmp_path / filename).read_text()
        assert published == regenerated, (
            f"{filename} is stale; run the schema-export script to regenerate "
            f"common-config/schemas/{filename}"
        )


def test_schema_export_module_can_run_as_a_script():
    module_path = (
        Path(__file__).parents[4]
        / "src"
        / "mapwisefox"
        / "common"
        / "config"
        / "_schema_export.py"
    )

    runpy.run_path(str(module_path), run_name="__main__")
