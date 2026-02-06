from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
env_path= Path(__file__).parent.parent / ".env"
class Settings(BaseSettings):

    APP_NAME: str
    APP_VERSION: str
    OPENAI_API_KEY: str

    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int

    class Config:

        env_file =env_path

def get_settings():
    return Settings()