from fastapi import Header, HTTPException, status
from typing import Optional
from config import settings


async def verify_api_key(x_api_key: Optional[str] = Header(default=None)):
    """
    Authentification simple par clé API (en-tête X-API-Key).
    Désactivée si MCP_API_KEY n'est pas définie dans l'environnement
    (pratique pour le développement local et les tests).
    """
    if settings.mcp_api_key is None:
        return

    if x_api_key != settings.mcp_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou manquante (en-tête X-API-Key requis)",
        )
