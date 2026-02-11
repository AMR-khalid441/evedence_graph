from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from domain import Paper


class PaperRepository(ABC):
    """
    Abstraction for persisting scraped papers.

    This allows swapping out the storage mechanism (JSON folder, Mongo, etc.)
    without changing scraping logic.
    """

    @abstractmethod
    def save(self, paper: Paper) -> None:
        """Persist a single paper instance."""
        raise NotImplementedError

    def save_many(self, papers: Iterable[Paper]) -> None:
        """
        Persist multiple papers.

        Default implementation just iterates and calls `save`, but
        implementations may override for batching/optimization.
        """

        for paper in papers:
            self.save(paper)

