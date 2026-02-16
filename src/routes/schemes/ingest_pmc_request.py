from pydantic import BaseModel
from typing import Optional


class IngestPmcRequest(BaseModel):
    """
    Request body for ingesting a PMC article: chunk → embed → vector DB.

    - doc_id: ID of the JSON article file (without .json extension)
    - collection_name: target vector DB collection name
    - chunk_size: target maximum length for each chunk body (in characters)
    - overlap_size: overlap length between consecutive chunks (in characters)
    """

    doc_id: str
    collection_name: str
    chunk_size: Optional[int] = 800
    overlap_size: Optional[int] = 80
