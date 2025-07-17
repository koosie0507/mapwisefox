from pathlib import Path

from lark import Lark


class QueryParser:
    def __init__(self):
        lark_grammar_path = Path(__file__).parent / "grammar.lark"
        grammar = lark_grammar_path.read_text(encoding="utf-8")
        self._lark = Lark(grammar)

    def parse(self, input_text):
        return self._lark.parse(input_text)