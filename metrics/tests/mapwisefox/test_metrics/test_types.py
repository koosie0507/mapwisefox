from mapwisefox.metrics._types import CommonArgs


def test_common_args_defaults():
    args = CommonArgs()

    assert args.input_files == []
    assert args.target_attrs == []
    assert args.id_attr == "id"
    assert args.output_file is None
    assert args.extra_cols == []
    assert args.input_dfs == []


def test_common_args_accepts_output_path(tmp_path):
    args = CommonArgs(output_file=tmp_path / "out.xlsx")
    assert args.output_file == tmp_path / "out.xlsx"
