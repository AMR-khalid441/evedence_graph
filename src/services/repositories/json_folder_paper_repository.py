from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from domain import Paper
from services.interfaces import PaperRepository


class JsonFolderPaperRepository(PaperRepository):
    """
    Stores `Paper` instances as JSON files in a folder.

    The JSON schema is kept identical to the existing files in `pmc_articles/`:
    {
        "doc_id": "...",
        "doc_title": "...",
        "source_url": "...",
        "created_at": "YYYY-MM-DD",
        "sections": [
            {"title": "...", "order": 0, "text": "..."},
            ...
        ]
    }
    """

    def __init__(self, folder: Union[str, Path]) -> None:
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)

    def save(self, paper: Paper) -> None:
        data = paper.to_dict()
        filename = self.folder / f"{data['doc_id']}.json"

        with filename.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

