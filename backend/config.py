from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Optionnel au démarrage : permet de déployer l'app sans clé, les
    # testeurs peuvent ensuite renseigner OPENAI_API_KEY sur la plateforme
    # d'hébergement. Sans clé valide, /mcp/chat répondra 502.
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    app_env: str = "development"
    # Si défini, les endpoints /mcp/* exigent l'en-tête "X-API-Key".
    # Laisser vide en développement local pour ne pas bloquer les tests.
    mcp_api_key: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()