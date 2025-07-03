from abc import ABCMeta, abstractmethod


class QueryBuilderAdapter(metaclass=ABCMeta):
    def __init__(self):
        self._stack = []

    def visit_start_group(self, group):
        self._stack.append([])  # start a new child list

    def visit_term(self, term):
        self._stack[-1].append(term)

    def visit_end_group(self, group):
        buf = self._stack.pop()
        self._process_current_buffer(buf, group)

    @abstractmethod
    def _process_current_buffer(self, buffer, group):
        raise NotImplementedError()
