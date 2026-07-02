from __future__ import annotations

from abc import ABC, abstractmethod


class JobExecutionBackend(ABC):
    @abstractmethod
    def submit(self, job_request: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def status(self, job_id: str) -> dict:
        raise NotImplementedError

