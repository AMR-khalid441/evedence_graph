from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Section:
    """
    Represents a single section of a paper.

    This is designed to match the existing JSON schema in `pmc_articles/`:
    {
        "title": "Results",
        "order": 0,
        "text": "full section text..."
    }
    """

    title: str
    order: int
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "order": self.order,
            "text": self.text,
        }


@dataclass
class Paper:
    """
    Domain model for a scraped PMC paper.

    Matches the existing JSON schema used in `pmc_articles/`:
    {
        "doc_id": "...",
        "doc_title": "...",
        "source_url": "...",
        "created_at": "YYYY-MM-DD",
        "sections": [Section, ...]
    }
    """

    doc_id: str
    doc_title: str
    source_url: str
    created_at: str  # keep as string to match existing JSON exactly
    sections: List[Section] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "doc_title": self.doc_title,
            "source_url": self.source_url,
            "created_at": self.created_at,
            "sections": [section.to_dict() for section in self.sections],
        }

