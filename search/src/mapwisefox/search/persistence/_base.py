from abc import ABCMeta, abstractmethod
from typing import Protocol


class PersistenceAdapter(Protocol, metaclass=ABCMeta):
    @abstractmethod
    def save(self, obj):
        raise NotImplementedError()
