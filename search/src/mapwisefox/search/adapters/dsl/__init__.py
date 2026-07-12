from mapwisefox.search.parser import Parser
from ._base import DSLAdapter


parse = Parser()


def run_dsl(dsl_text: str, adapter: DSLAdapter) -> dict | str:
    """
    Parse a DSL string and run it through the given adapter.

    Returns either a plain string (no output_spec) or a dict
    keyed by OutputTarget when an output_spec_expr is present.
    """
    ir = parse(dsl_text)
    return adapter.adapt(ir)


