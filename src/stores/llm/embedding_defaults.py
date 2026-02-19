"""Provider defaults for embedding models and dimensions."""

EMBEDDING_DEFAULTS = {
    "OPENAI": ("text-embedding-3-large", 3072),
    "COHERE": ("embed-english-v3.0", 1024),
    "SENTENCE_TRANSFORMERS": ("neuml/pubmedbert-base-embeddings", 768),
}

# Map embedding dimension -> provider (for auto-detect from collection)
DIMENSION_TO_PROVIDER = {size: provider for provider, (_, size) in EMBEDDING_DEFAULTS.items()}
