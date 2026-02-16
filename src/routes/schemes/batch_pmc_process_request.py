from pydantic import BaseModel
from typing import Optional


class BatchPmcProcessRequest(BaseModel):
    """
    Request body for batch processing stored PMC JSON articles.

    - doc_ids: list of doc_id (JSON article file names without .json extension)
    - chunk_size: target maximum length for each chunk body (in characters)
    - overlap_size: overlap length between consecutive chunks (in characters)
    """

    doc_ids: list[str]
    chunk_size: Optional[int] = 800
    overlap_size: Optional[int] = 80
