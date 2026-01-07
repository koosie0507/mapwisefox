from pathlib import Path

import click

from mapwisefox.metrics import _utils as util


def _check_path_supported(param_name: str, value: str | Path, supported: set):
    path = Path(value).resolve()
    if path.suffix not in supported:
        raise click.BadParameter(f"{param_name} does not support {path.suffix!r} files")
    return path


def validate_input_file_type(ctx, param, value):
    if isinstance(value, (list, tuple, set, frozenset)):
        return [
            _check_path_supported(param.name, x, util.SUPPORTED_FILE_HANDLERS)
            for x in value
        ]
    if isinstance(value, (str, Path)):
        return _check_path_supported(param.name, value, util.SUPPORTED_FILE_HANDLERS)
    raise click.BadParameter(
        f"{param.name} must be a str a path or a list of either of those", ctx
    )


def validate_output_file_type(_, param, value):
    return _check_path_supported(param.name, value, {".xls", ".xlsx"})
