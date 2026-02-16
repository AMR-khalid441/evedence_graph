from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from qdrant_client import QdrantClient

from helpers.config import get_settings, Settings
from stores.llm.llm_provider_factory import LLMProviderFactory
from .schemes import SearchRequest, QueryRequest


nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)


class RetrievedDocument(BaseModel):
    text: str
    metadata: dict
    score: float


def _get_qdrant_client(app_settings: Settings) -> QdrantClient:
    """
    Create QdrantClient - Qdrant Cloud required (QDRANT_CLUSTER_URL and QDRANT_KEY).
    """
    url = getattr(app_settings, 'QDRANT_CLUSTER_URL', None) or ''
    api_key = getattr(app_settings, 'QDRANT_KEY', None) or ''
    if not url or not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Qdrant Cloud is required. Set QDRANT_CLUSTER_URL and QDRANT_KEY in your .env file.",
        )
    return QdrantClient(url=url, api_key=api_key)


def _embed_query(query: str, app_settings: Settings):
    """
    Use the configured LLM provider to embed a query string.
    Returns (llm, query_vector).
    """
    llm_factory = LLMProviderFactory(app_settings)
    llm = llm_factory.create(app_settings.LLM_PROVIDER)
    if llm is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM provider not available: {app_settings.LLM_PROVIDER}",
        )
    llm.set_embedding_model(app_settings.EMBEDDING_MODEL_ID, app_settings.EMBEDDING_SIZE)

    vec = llm.embed_text(query)
    if vec is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Embedding failed for query",
        )
    return llm, vec


@nlp_router.post("/search")
async def nlp_search_endpoint(
    request: SearchRequest,
    app_settings: Settings = Depends(get_settings),
):
    """
    Semantic search endpoint using official Qdrant query_points method.
    - Embeds the query via LLMProviderFactory.
    - Uses Qdrant's query_points() method for similarity search.
    - Returns chunks with text, metadata, and score.
    """
    # Embed query
    _, query_vector = _embed_query(request.query, app_settings)

    client = _get_qdrant_client(app_settings)

    # Ensure collection exists
    if not client.collection_exists(request.collection_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{request.collection_name}' does not exist",
        )

    # Use official Qdrant query_points method - handles similarity calculation automatically
    try:
        resp = client.query_points(
            collection_name=request.collection_name,
            query=query_vector,
            limit=request.limit,
            with_payload=True,
        )
        hits = resp.points
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Qdrant search failed: {e}",
        )

    # Convert hits to response format
    chunks = []
    for hit in hits:
        payload = hit.payload or {}
        text = payload.get("text", "")
        metadata = payload.get("metadata", {}) or {}
        chunks.append(
            {
                "text": text,
                "metadata": metadata,
                "score": hit.score,  # Score already calculated by Qdrant
            }
        )

    return {"chunks": chunks}


@nlp_router.post("/query")
async def nlp_query_endpoint(
    request: QueryRequest,
    app_settings: Settings = Depends(get_settings),
):
    """
    RAG query endpoint using official Qdrant query_points method.
    - Embeds the query.
    - Uses Qdrant's query_points() for similarity search.
    - Builds a prompt from the top-k retrieved chunks.
    - Generates an answer with llm.generate_text.
    - Returns answer and chunks_used.
    """
    # LLM + embedding
    llm, query_vector = _embed_query(request.query, app_settings)

    client = _get_qdrant_client(app_settings)

    if not client.collection_exists(request.collection_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{request.collection_name}' does not exist",
        )

    # Use official Qdrant query_points method - handles similarity calculation automatically
    try:
        resp = client.query_points(
            collection_name=request.collection_name,
            query=query_vector,
            limit=request.limit,
            with_payload=True,
        )
        hits = resp.points
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Qdrant search failed: {e}",
        )

    if not hits:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No relevant chunks found",
        )

    # Convert hits to RetrievedDocument format
    chunks_used: list[RetrievedDocument] = []
    for hit in hits:
        payload = hit.payload or {}
        text = payload.get("text", "")
        metadata = payload.get("metadata", {}) or {}
        chunks_used.append(
            RetrievedDocument(text=text, metadata=metadata, score=hit.score)
        )

    # Build prompt from chunks
    chunk_texts = "\n\n---\n\n".join(
        f"[{i+1}] {doc.text}" for i, doc in enumerate(chunks_used)
    )
    prompt = (
        "Answer the question based only on the following excerpts. "
        "If the excerpts do not contain enough information, say so.\n\n"
        f"Question: {request.query}\n\n"
        f"Excerpts:\n{chunk_texts}"
    )

    # Generation model
    llm.set_generation_model(app_settings.GENERATION_MODEL_ID)
    answer = llm.generate_text(prompt, chat_history=[])
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Generation failed",
        )

    return {
        "answer": answer,
        "chunks_used": [doc.model_dump() for doc in chunks_used],
    }