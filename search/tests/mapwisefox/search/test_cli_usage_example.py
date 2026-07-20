import pytest


def test_basic_usage_cli_exits_successfully(basic_usage_result):
    assert (
        basic_usage_result.exit_code == 0
    ), f"CLI exited {basic_usage_result.exit_code}; output:\n{basic_usage_result.output}"
    if basic_usage_result.exception:
        raise basic_usage_result.exception


@pytest.mark.parametrize(
    "adapter_name",
    [
        "AcmDSLAdapter",
        "XploreDSLAdapter",
        "ScienceDirectDSLAdapter",
        "ScopusDSLAdapter",
        "SpringerDSLAdapter",
        "WebOfScienceDSLAdapter",
    ],
)
def test_console_output_contains_expected_query_block(
    basic_usage_result,
    ersa_query_objects_by_adapter,
    render_console_block,
    adapter_name,
):
    query_obj = ersa_query_objects_by_adapter[adapter_name]
    expected_block = render_console_block(query_obj)

    assert expected_block in basic_usage_result.output, (
        f"Expected console block for {adapter_name} not found in CLI output.\n\n"
        f"Expected block:\n{expected_block}\n\n"
        f"Full CLI output:\n{basic_usage_result.output}"
    )


def test_console_backends_run_in_config_order(
    basic_usage_result, ersa_query_objects_by_adapter, render_console_block
):
    ordered_adapters = [
        "AcmDSLAdapter",
        "XploreDSLAdapter",
        "ScienceDirectDSLAdapter",
        "ScopusDSLAdapter",
        "SpringerDSLAdapter",
        "WebOfScienceDSLAdapter",
    ]

    blocks = [
        render_console_block(ersa_query_objects_by_adapter[name])
        for name in ordered_adapters
    ]

    indices = [basic_usage_result.output.index(block) for block in blocks]
    assert indices == sorted(indices), (
        f"Console blocks did not appear in config order. "
        f"Found indices: {indices} (expected ascending order)"
    )
