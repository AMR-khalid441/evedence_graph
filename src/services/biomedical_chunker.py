"""
Biomedical research paper chunker optimized for PubMedBERT embeddings.

Chunks are designed for:
- Semantic search (PubMedBERT embeddings): coherent, self-contained text
- Hybrid search (keyword/BM25): avoids mid-word splits, preserves phrases
- Reranker: each chunk is independently scorable with clear boundaries

Output schema is JSON-compatible for direct use in vector DB, hybrid indexes,
and downstream reranking pipelines.
"""

from __future__ import annotations

import re
from typing import Any

# Lazy-load tokenizer to avoid import cost when chunker is not used
_TOKENIZER = None

# PubMedBERT max seq length; we use 480 to leave headroom for special tokens
MAX_CHUNK_TOKENS = 480
OVERLAP_TOKENS = 80
WORD_OVERLAP = 10

# Placeholder to protect periods in abbreviations/decimals during sentence split
_PROTECT_PLACEHOLDER = "\uE000"  # Unicode private use


def _get_tokenizer():
    """Lazy-load PubMedBERT tokenizer. Uses same vocab as embedding model."""
    global _TOKENIZER
    if _TOKENIZER is None:
        from transformers import AutoTokenizer

        _TOKENIZER = AutoTokenizer.from_pretrained("neuml/pubmedbert-base-embeddings")
    return _TOKENIZER


def _token_count(text: str) -> int:
    """Return token count for text using PubMedBERT tokenizer."""
    if not text or not str(text).strip():
        return 0
    return len(_get_tokenizer().encode(text, add_special_tokens=False))


def _protect_periods(text: str) -> str:
    """Replace periods in decimals/abbreviations with placeholder to avoid false splits."""
    # Decimals: 0.05, 1.23, p=0.001
    text = re.sub(r"(\d)\.(\d)", r"\1" + _PROTECT_PLACEHOLDER + r"\2", text)
    # Abbreviations: Fig., et al., Dr., e.g., i.e., vs., No.
    text = re.sub(
        r"(Fig|Figs|et\s+al|Dr|Mr|Mrs|Ms|e\.g|i\.e|vs|No)\.(\s|$)",
        r"\1" + _PROTECT_PLACEHOLDER + r"\2",
        text,
        flags=re.IGNORECASE,
    )
    return text


def _restore_periods(text: str) -> str:
    """Restore protected periods."""
    return text.replace(_PROTECT_PLACEHOLDER, ".")


def _split_sentences_scientific(text: str) -> list[str]:
    """
    Split text into sentences using a scientific-aware splitter.

    Protects:
    - Decimals (0.05, 1.23)
    - Abbreviations: Fig., Figs., et al., Dr., e.g., i.e., vs., No.
    - Statistics: p < 0.05, p = 0.001 (decimals protected above)
    """
    if not text or not str(text).strip():
        return []

    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    protected = _protect_periods(text)
    # Split on . ! ? when followed by space and uppercase (sentence start)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])$", protected)
    sentences = [_restore_periods(p.strip()) for p in parts if p.strip()]
    return sentences


def _split_long_sentence_wordwise(text: str, max_tokens: int, word_overlap: int) -> list[str]:
    """
    Split a single long sentence into token-safe pieces using word boundaries.

    Uses word-level overlap to preserve context for hybrid search and reranker.
    """
    words = text.split()
    if not words:
        return []
    tokenizer = _get_tokenizer()
    chunks = []
    start = 0
    while start < len(words):
        # Grow chunk until we hit max_tokens
        end = start
        chunk_words = []
        while end < len(words):
            candidate = chunk_words + [words[end]]
            candidate_text = " ".join(candidate)
            if _token_count(candidate_text) > max_tokens and chunk_words:
                break
            chunk_words = candidate
            end += 1
        if chunk_words:
            chunks.append(" ".join(chunk_words))
        # Overlap: step back by word_overlap (or to start+1 if sentence is very long)
        start = end - word_overlap if end - word_overlap > start else start + len(chunk_words)
        if start >= len(words):
            break
    return chunks


def _chunk_section_text(
    section_text: str,
    max_tokens: int = MAX_CHUNK_TOKENS,
    overlap_tokens: int = OVERLAP_TOKENS,
    word_overlap: int = WORD_OVERLAP,
) -> list[str]:
    """
    Chunk section text into token-safe pieces.

    - Splits by sentences (scientific-aware).
    - Each chunk <= max_tokens with overlap_tokens overlap.
    - If a sentence exceeds max_tokens, splits it word-wise with word_overlap.
    - Never produces a chunk > 512 tokens (PubMedBERT limit).
    """
    sentences = _split_sentences_scientific(section_text)
    if not sentences:
        return []

    chunks = []
    current_sentences = []
    current_tokens = 0
    overlap_sentences = []

    def flush_chunk() -> str | None:
        nonlocal current_sentences, overlap_sentences
        if not current_sentences:
            return None
        text = " ".join(current_sentences).strip()
        if not text:
            return None
        # Ensure we never exceed 512
        if _token_count(text) > 512:
            # Fallback: split current content word-wise
            return None  # Caller will handle
        overlap_sentences = _get_overlap_sentences(current_sentences, overlap_tokens)
        return text

    def _get_overlap_sentences(sents: list[str], target_overlap: int) -> list[str]:
        """Return trailing sentences that approximate target_overlap tokens."""
        result = []
        count = 0
        for s in reversed(sents):
            if count >= target_overlap:
                break
            result.insert(0, s)
            count += _token_count(s)
        return result

    i = 0
    while i < len(sentences):
        sent = sentences[i]
        sent_tokens = _token_count(sent)

        # Single sentence exceeds max_tokens: split word-wise
        if sent_tokens > max_tokens:
            # Flush any current chunk first
            if current_sentences:
                t = flush_chunk()
                if t:
                    chunks.append(t)
                current_sentences = []
                current_tokens = 0
            sub_chunks = _split_long_sentence_wordwise(sent, max_tokens, word_overlap)
            for sc in sub_chunks:
                if _token_count(sc) <= 512:
                    chunks.append(sc)
            overlap_sentences = sub_chunks[-1].split()[-word_overlap:] if sub_chunks else []
            current_sentences = [" ".join(overlap_sentences)] if overlap_sentences else []
            current_tokens = _token_count(current_sentences[0]) if current_sentences else 0
            i += 1
            continue

        # Would exceed max_tokens: flush current chunk and start new with overlap
        if current_tokens + sent_tokens > max_tokens and current_sentences:
            t = flush_chunk()
            if t:
                chunks.append(t)
            current_sentences = overlap_sentences.copy()
            current_tokens = sum(_token_count(s) for s in current_sentences)
            continue

        current_sentences.append(sent)
        current_tokens += sent_tokens
        i += 1

    if current_sentences:
        t = flush_chunk()
        if t and _token_count(t) <= 512:
            chunks.append(t)

    return chunks


def chunk_section(
    section_text: str,
    doc_id: str,
    doc_title: str,
    source_url: str,
    section_title: str,
    section_order: int,
    max_tokens: int = MAX_CHUNK_TOKENS,
    overlap_tokens: int = OVERLAP_TOKENS,
    word_overlap: int = WORD_OVERLAP,
) -> list[dict[str, Any]]:
    """
    Chunk a single section into token-safe pieces.

    Section title and paper title are stored ONLY in metadata, not in chunk text.
    This keeps chunk text focused for semantic search while metadata supports
    filtering and hybrid keyword search on section names.
    """
    if not section_text or not str(section_text).strip():
        return []

    raw_chunks = _chunk_section_text(
        section_text,
        max_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
        word_overlap=word_overlap,
    )

    result = []
    for idx, text in enumerate(raw_chunks):
        # Final safety: never exceed 512 tokens
        if _token_count(text) > 512:
            sub = _split_long_sentence_wordwise(text, 480, word_overlap)
            for j, s in enumerate(sub):
                result.append(
                    {
                        "text": s.strip(),
                        "metadata": {
                            "doc_id": doc_id,
                            "doc_title": doc_title,
                            "source_url": source_url,
                            "section_title": section_title,
                            "section_order": section_order,
                            "chunk_index": idx if len(sub) == 1 else idx * 10 + j,
                        },
                    }
                )
        else:
            result.append(
                {
                    "text": text.strip(),
                    "metadata": {
                        "doc_id": doc_id,
                        "doc_title": doc_title,
                        "source_url": source_url,
                        "section_title": section_title,
                        "section_order": section_order,
                        "chunk_index": idx,
                    },
                }
            )
    return result


def chunk_paper_sections(
    sections: dict[str, str],
    doc_id: str,
    doc_title: str,
    source_url: str = "",
    max_tokens: int = MAX_CHUNK_TOKENS,
    overlap_tokens: int = OVERLAP_TOKENS,
    word_overlap: int = WORD_OVERLAP,
) -> list[dict[str, Any]]:
    """
    Wrapper: chunk a paper from a dictionary of section name -> section text.

    Args:
        sections: e.g. {"Results": "...", "Discussion": "...", "Conclusions": "..."}
        doc_id: Unique document identifier
        doc_title: Full paper title
        source_url: Paper URL or source
        max_tokens: Max tokens per chunk (default 480)
        overlap_tokens: Overlap between chunks (default 80)
        word_overlap: Word overlap when splitting long sentences (default 10)

    Returns:
        List of chunks, each with "text" and "metadata" in JSON-compatible schema.
    """
    all_chunks = []
    section_order = 0
    for section_title, section_text in sections.items():
        if not section_title or not str(section_text).strip():
            section_order += 1
            continue
        chunks = chunk_section(
            section_text=section_text,
            doc_id=doc_id,
            doc_title=doc_title,
            source_url=source_url,
            section_title=section_title,
            section_order=section_order,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
            word_overlap=word_overlap,
        )
        all_chunks.extend(chunks)
        section_order += 1
    return all_chunks
