import logging

from mapwisefox.assistant.tools.callbacks import (
    make_stderr_callback,
    make_thinking_callback,
    write_stdout,
)


def test_write_stdout_echoes_plain_message(capsys):
    write_stdout("hello")

    assert capsys.readouterr().out == "hello"


def test_write_stdout_interpolates_args(capsys):
    write_stdout("hello %s", "world")

    assert capsys.readouterr().out == "hello world"


def test_thinking_callback_prints_label_once_on_first_call(capsys):
    callback = make_thinking_callback()

    callback("first thought")

    assert "Thinking" in capsys.readouterr().out


def test_thinking_callback_omits_label_on_subsequent_calls(capsys):
    callback = make_thinking_callback()
    callback("first thought")
    capsys.readouterr()

    callback("second thought")

    assert "Thinking" not in capsys.readouterr().out


def test_stderr_callback_logs_with_exception_info(caplog):
    logger = logging.getLogger("test-stderr-callback")
    callback = make_stderr_callback(logger)
    error = ValueError("boom")

    with caplog.at_level(logging.ERROR, logger="test-stderr-callback"):
        callback("something failed", error)

    assert "something failed" in caplog.text
