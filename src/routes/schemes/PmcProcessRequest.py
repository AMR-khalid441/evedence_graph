from pydantic import BaseModel
from typing import Optional


class PmcProcessRequest(BaseModel):
    """
    Request body for processing a stored PMC JSON article.

    - doc_id: ID of the JSON article file (without .json extension)
    - chunk_size: target maximum length for each chunk body (in characters)
    - overlap_size: overlap length between consecutive chunks (in characters)
    """

    doc_id: str
    chunk_size: Optional[int] = 800
    overlap_size: Optional[int] = 80

