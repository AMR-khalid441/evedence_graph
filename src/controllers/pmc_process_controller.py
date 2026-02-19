import json
from pathlib import Path
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .base_controller import BaseController


class PmcProcessController(BaseController):
    """
    Controller responsible for processing stored PMC JSON articles
    into semantically chunked sections suitable for downstream use.
    """

    def __init__(self):
        super().__init__()
        # `base_dir` from BaseController points at the `src` directory.
        # PMC JSON articles live in the project-level `pmc_articles/` folder.
        self.pmc_articles_dir = Path(self.base_dir).parent / "pmc_articles"

    def list_doc_ids(self) -> List[str]:
        """
        Return sorted list of available PMC doc_ids (JSON filenames without .json).
        """
        if not self.pmc_articles_dir.exists():
            return []
        return sorted(p.stem for p in self.pmc_articles_dir.glob("*.json"))

    def _load_article(self, doc_id: str) -> dict:
        """
        Load a PMC article JSON by its doc_id (without .json extension).
        """
        path = self.pmc_articles_dir / f"{doc_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"PMC article not found for doc_id={doc_id}: {path}")

        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def load_article(self, doc_id: str) -> dict:
        """Load a PMC article JSON by doc_id. Public wrapper for _load_article."""
        return self._load_article(doc_id=doc_id)

    def process_article(
        self,
        doc_id: str,
        chunk_size: int = 800,
        overlap_size: int = 80,
    ):
        """
        Process a stored PMC JSON article into semantically split chunks.

        The article is processed per-section, never mixing content from
        different sections in the same chunk. Each chunk's page_content
        is prefixed with the article and section titles.

        chunk_size and overlap_size are in characters.
        """
        article = self._load_article(doc_id=doc_id)

        doc_title = article.get("doc_title", "")
        source_url = article.get("source_url", "")
        sections = article.get("sections", [])

        all_chunks: List = []
        global_chunk_index = 0

        for section in sections:
            section_title = section.get("title", "")
            section_order = section.get("order", 0)
            section_text = section.get("text", "") or ""

            # Prefix to add to every chunk so each has clear context.
            prefix = f"{doc_title}\n\n{section_title}\n\n"

            # Reserve space for the prefix when splitting the body text.
            reserved_len = len(prefix)
            body_chunk_size = max(1, chunk_size - reserved_len)

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=body_chunk_size,
                chunk_overlap=overlap_size,
                length_function=len,
                separators=["\n\n", "\n", ". ", " "],
            )

            # First split only the body text for this section.
            docs = text_splitter.create_documents(
                texts=[section_text],
                metadatas=[
                    {
                        "doc_id": article.get("doc_id"),
                        "doc_title": doc_title,
                        "source_url": source_url,
                        "section_title": section_title,
                        "section_order": section_order,
                    }
                ],
            )

            # Now prepend the titles to each chunk's content and attach a chunk index.
            for doc in docs:
                doc.page_content = prefix + doc.page_content
                # Attach a per-article chunk index for easier debugging / tracing.
                doc.metadata["chunk_index"] = global_chunk_index
                global_chunk_index += 1

            all_chunks.extend(docs)

        return all_chunks
