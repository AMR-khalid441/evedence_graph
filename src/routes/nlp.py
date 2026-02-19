from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from qdrant_client import QdrantClient

from src.helpers.config import get_settings, Settings
from src.stores.llm.embedding_defaults import EMBEDDING_DEFAULTS, DIMENSION_TO_PROVIDER
from src.stores.llm.llm_provider_factory import LLMProviderFactory
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
    url = getattr(app_settings, 'QDRANT_CLUSTER_URL', None) or ''
    api_key = getattr(app_settings, 'QDRANT_KEY', None) or ''
    if not url or not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Qdrant Cloud is required. Set QDRANT_CLUSTER_URL and QDRANT_KEY in your .env file.",
        )
    return QdrantClient(url=url, api_key=api_key)


def _get_provider_for_collection(client, collection_name: str, app_settings: Settings) -> str:
    """Auto-detect embedding provider from collection's vector dimension."""
    info = client.get_collection(collection_name=collection_name)
    params = getattr(info, "config", None) and getattr(info.config, "params", None)
    if not params or not params.vectors:
        return app_settings.LLM_PROVIDER
    vectors_cfg = params.vectors
    if hasattr(vectors_cfg, "size"):
        size = vectors_cfg.size
    elif isinstance(vectors_cfg, dict):
        first = next(iter(vectors_cfg.values()), None)
        size = getattr(first, "size", None) if first else None
    else:
        return app_settings.LLM_PROVIDER
    return DIMENSION_TO_PROVIDER.get(size, app_settings.LLM_PROVIDER)


def _embed_query(query: str, app_settings: Settings, embedding_provider: str | None = None, collection_name: str | None = None, client=None):
    if embedding_provider:
        provider = embedding_provider
    elif collection_name and client:
        provider = _get_provider_for_collection(client, collection_name, app_settings)
    else:
        provider = app_settings.LLM_PROVIDER
    defaults = EMBEDDING_DEFAULTS.get(provider)
    if defaults:
        model_id, embedding_size = defaults
    else:
        model_id = app_settings.EMBEDDING_MODEL_ID
        embedding_size = app_settings.EMBEDDING_SIZE

    llm_factory = LLMProviderFactory(app_settings)
    llm = llm_factory.create(provider)
    if llm is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM provider not available: {provider}",
        )
    llm.set_embedding_model(model_id, embedding_size)

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
    - Auto-detects embedding provider from collection vector size when not specified.
    - Uses Qdrant's query_points() method for similarity search.
    - Returns chunks with text, metadata, and score.
    """
    client = _get_qdrant_client(app_settings)

    if not client.collection_exists(request.collection_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{request.collection_name}' does not exist",
        )

    _, query_vector = _embed_query(
        request.query,
        app_settings,
        request.embedding_provider,
        request.collection_name,
        client,
    )

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

    threshold = request.min_score_threshold
    chunks = []
    for hit in hits:
        payload = hit.payload or {}
        text = payload.get("text", "")
        metadata = payload.get("metadata", {}) or {}
        similarity = max(0.0, min(1.0, hit.score))
        if threshold is not None and similarity < threshold:
            continue
        chunks.append({"text": text, "metadata": metadata, "score": similarity})

    return {"chunks": chunks}


@nlp_router.post("/query")
async def nlp_query_endpoint(
    request: QueryRequest,
    app_settings: Settings = Depends(get_settings),
):
    """
    RAG query endpoint using official Qdrant query_points method.
    - Embeds the query. Auto-detects embedding provider from collection when not specified.
    - Uses Qdrant's query_points() for similarity search.
    - Filters chunks below app_settings.MIN_SCORE_THRESHOLD.
    - Builds a prompt from the top-k retrieved chunks.
    - Generates an answer with llm.generate_text.
    - Returns answer and chunks_used.
    """
    client = _get_qdrant_client(app_settings)

    if not client.collection_exists(request.collection_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{request.collection_name}' does not exist",
        )

    llm, query_vector = _embed_query(
        request.query,
        app_settings,
        request.embedding_provider,
        request.collection_name,
        client,
    )

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

    # Filter out low-relevance chunks
    threshold = request.min_score_threshold or app_settings.MIN_SCORE_THRESHOLD
    chunks_used: list[RetrievedDocument] = []
    for hit in hits:
        payload = hit.payload or {}
        text = payload.get("text", "")
        metadata = payload.get("metadata", {}) or {}
        similarity = max(0.0, min(1.0, hit.score))

        if similarity >= threshold:
            chunks_used.append(
                RetrievedDocument(text=text, metadata=metadata, score=similarity)
            )

    if not chunks_used:
        return {
            "answer": "I don't have enough information to answer this question.",
            "chunks_used": [],
        }

    # Label each chunk with its relevance score
    chunk_texts = "\n\n---\n\n".join(
        f"[{i+1}] (Relevance: {doc.score:.2f})\n{doc.text}"
        for i, doc in enumerate(chunks_used)
    )

    prompt = f"""You are a question-answering assistant. Your ONLY job is to extract and return the answer from the excerpts provided below.

STRICT RULES — follow these exactly:
- You MUST answer using the excerpts. They are your only source of truth.
- If the answer is present in the excerpts, state it clearly and directly. Do NOT say you lack information.
- Excerpts with a Relevance score above 0.60 are highly relevant — treat them as authoritative.
- Cite the excerpt number inline (e.g. "According to [1]...").
- After your answer, add a single line: "Confidence: X%" where X reflects how completely the excerpts cover the question (90-100% if fully answered, 50-89% if partially, below 50% if very incomplete).
- Only say "I don't have enough information to answer this question." if NONE of the excerpts contain any information related to the question whatsoever.
- Do NOT make up or infer any statistics, names, or facts not explicitly written in the excerpts.

QUESTION:
{request.query}

EXCERPTS:
{chunk_texts}

ANSWER:"""


    llm.default_input_max_characters = len(prompt) + 100

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