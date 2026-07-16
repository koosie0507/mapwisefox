import pytest


@pytest.fixture
def query_object(request, parse, stub_adapter):
    text = getattr(request, "param", "")
    return stub_adapter.adapt(parse(text))


@pytest.mark.parametrize(
    "query_object,fields,regex",
    [
        (r'match[regex]("a\s+b")', [""], r"a\s+b"),
        (r'match[regex]("a\s+b") in title', ["title"], r"a\s+b"),
        (r'match[regex]("a\s+b") in title,keywords', ["title", "keywords"], r"a\s+b"),
        (r'(match[regex]("a\s+b")) in title,keywords', ["title", "keywords"], r"a\s+b"),
    ],
    indirect=["query_object"],
)
def test_match_regex(query_object, fields, regex):
    assert query_object.query == ""
    for f in fields:
        assert f in query_object.regex, f"{f} not in regex"
        assert query_object.regex[f] == regex, f"{f} regex is not '{regex}'"


@pytest.mark.parametrize(
    "query_object,stub_adapter,query,fields,regex",
    [
        (
            r'"amazing" in regex_field',
            (["regex_field"],),
            "",
            ["regex_field"],
            r"amazing",
        ),
        (
            r'!"amazing" in regex_field',
            (["regex_field"],),
            "",
            ["regex_field"],
            r"^(?!.*amazing)",
        ),
        (
            r'"amazing" in regex_field,normal',
            (["regex_field"],),
            "VAL(amazing in ['normal'])",
            ["regex_field"],
            r"amazing",
        ),
        (
            r'"amazing" in regex_field & "b" in normal',
            (["regex_field"],),
            "VAL(b in ['normal'])",
            ["regex_field"],
            r"amazing",
        ),
        (
            r'"a" in regex_field & (("b" in normal) | ("c" in regex_field))',
            (["regex_field"],),
            "(VAL(b in ['normal']))",
            ["regex_field"],
            r"^(?=.*a)(?=.*c)",
        ),
        (
            r'"a" in regex_field & ("b" in normal | !"c" in regex_field)',
            (["regex_field"],),
            "(VAL(b in ['normal']))",
            ["regex_field"],
            r"^(?=.*a)(?!.*c)",
        ),
        (
            r'"a" in regex_field & (!"b" in normal | "c" in regex_field)',
            (["regex_field"],),
            "(NOT VAL(b in ['normal']))",
            ["regex_field"],
            r"^(?=.*a)(?=.*c)",
        ),
        (
            r'("a"|"b") in regex_field & "c"',
            (["regex_field"],),
            "VAL(c)",
            ["regex_field"],
            r"(a|b)",
        ),
        (
            r'("a" in regex_field) in normal',
            (["regex_field"],),
            "",
            ["regex_field"],
            r"a",
        ),
        (
            r'("a"|("b"&"c")) in regex_field',
            (["regex_field"],),
            "",
            ["regex_field"],
            r"^(?=.*b)(?=.*c)a",
        ),
        (
            r'("a"|(!"b"&!"c")) in regex_field',
            (["regex_field"],),
            "",
            ["regex_field"],
            r"^(?!.*b)(?!.*c)a",
        ),
    ],
    indirect=["query_object", "stub_adapter"],
)
def test_regex_field_in_value_expr(query_object, stub_adapter, query, fields, regex):
    assert query_object.query == query
    for f in fields:
        assert f in query_object.regex, f"{f} not in regex"
        assert query_object.regex[f] == regex, f"{f} regex is not '{regex}'"
