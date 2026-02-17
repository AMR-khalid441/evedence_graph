from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env from src/ or project root (resolve to absolute path so it works from any cwd)
_base = Path(__file__).resolve().parent.parent  # src/
_env_src = _base / ".env"
_env_root = _base.parent / ".env"
env_path = _env_src if _env_src.exists() else _env_root

# Explicitly load .env file for robustness (before pydantic-settings reads it)
load_dotenv(_env_src, override=False)
load_dotenv(_env_root, override=False)


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    OPENAI_API_KEY: str

    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int

    # LLM store
    OPENAI_API_URL: Optional[str] = None
    INPUT_DEFAULT_MAX_CHARACTERS: int = 1000
    GENERATION_DEFAULT_MAX_TOKENS: int = 1000
    GENERATION_DEFAULT_TEMPERATURE: float = 0.1
    COHERE_API_KEY: str = ""

    # Vector DB store
    VECTOR_DB_PATH: str = "qdrant_data"
    VECTOR_DB_DISTANCE_METHOD: str = "cosine"
    QDRANT_KEY: Optional[str] = None  # API key for Qdrant Cloud
    QDRANT_CLUSTER_URL: Optional[str] = None  # Cloud cluster URL

    # Ingest (LLM + Vector DB for chunk → embed → store)
    LLM_PROVIDER: str = "OPENAI"
    VECTOR_DB_PROVIDER: str = "QDRANT"
    EMBEDDING_MODEL_ID: str = "text-embedding-3-large"  # Best accuracy: 0.811 vs 0.762 for small
    EMBEDDING_SIZE: int = 3072  # text-embedding-3-large uses 3072 dimensions
    GENERATION_MODEL_ID: str = "gpt-4o"  # Best accuracy: flagship model, better than gpt-4o-mini
    MIN_SCORE_THRESHOLD: float = 0.4  # Min similarity (0-1) for RAG chunks; chunks below this are filtered out

    model_config = SettingsConfigDict(
        env_file=str(env_path) if env_path.exists() else None,
        env_file_encoding='utf-8',
        case_sensitive=False,
    )

def get_settings():
    return Settings()