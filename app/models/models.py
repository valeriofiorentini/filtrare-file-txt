from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class FileDocument(BaseModel):
    """modello per il documento indicizzato"""
    nome_file: str
    contenuto_file: str
    percorso_completo: str

class Settings(BaseSettings):
    """carica le configurazioni del file .env"""
    ELASTICSEARCH_HOST: str
    INDEX_NAME: str
    DIRECTORY_PATH: str
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {function} | {line} | {message}"


    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

@lru_cache
def get_config() -> Settings:
    """ottiene l'istanza di configurazione, utilizzando una cache."""
    return Settings()

config = get_config()


