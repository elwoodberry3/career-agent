"""The interface every job source implements."""

from __future__ import annotations

from typing import Protocol

from zoe.models import Job


class SourceError(RuntimeError):
    """A source failed for this run. The orchestrator logs it and continues."""


class JobSource(Protocol):
    name: str

    def fetch(self) -> list[Job]:
        """Return jobs posted recently for every configured search.

        Must not raise for a single bad record (skip and log it).
        Raise SourceError if the source as a whole is unusable this run.
        """
        ...
