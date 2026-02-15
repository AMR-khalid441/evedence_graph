from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

env_path = Path(__file__).parent.parent / ".env"


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

    class Config:
        env_file = env_path

def get_settings():
    return Settings()