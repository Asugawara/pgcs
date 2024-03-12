from __future__ import annotations

from abc import ABCMeta, abstractmethod


class Entry(metaclass=ABCMeta):
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return self._name

    @abstractmethod
    def path(self) -> str:
        pass

    @abstractmethod
    def add(self, entry: Entry) -> None:
        pass
