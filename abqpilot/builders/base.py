from __future__ import annotations

from abc import ABC, abstractmethod


class Builder(ABC):
    @abstractmethod
    def build(self, build_request: dict) -> dict:
        raise NotImplementedError

