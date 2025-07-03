from abc import ABCMeta, abstractmethod
from io import StringIO

from mapwisefox.search.adapters._base import QueryBuilderAdapter


class FlatOutputAdapter(QueryBuilderAdapter, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        self._output = StringIO()

    def _write(self, value):
        if value is None or len(value) < 1:
            return

        if len(self._stack) > 0:
            self._stack[-1].append(value)
        else:
            self._output.write(value)

    def _process_current_buffer(self, buffer, group):
        text = self._extract_group_str(buffer, group)
        self._write(text)

    @abstractmethod
    def _extract_group_str(self, buf, group):
        raise NotImplementedError()

    def result(self):
        return self._output.getvalue()
