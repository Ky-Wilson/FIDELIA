from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    app_env: str = "development"
    # Si défini, les endpoints /mcp/* exigent l'en-tête "X-API-Key".
    # Laisser vide en développement local pour ne pas bloquer les tests.
    mcp_api_key: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()