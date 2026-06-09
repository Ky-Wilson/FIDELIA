import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from chat import chat_with_tools
from auth import verify_api_key
from tools.convert_currency import convert_currency
from tools.calculate_vat import calculate_vat
from tools.tax_deadlines import get_tax_deadlines
from tools.calculate_cnps import calculate_cnps
from tools.search_tax_code import search_tax_code

logger = logging.getLogger("fidelia.mcp")

router = APIRouter(dependencies=[Depends(verify_api_key)])

# --- Schémas ---
class ConvertCurrencyRequest(BaseModel):
    amount: float
    from_currency: str = "XOF"
    to_currency: str = "EUR"

class VatRequest(BaseModel):
    amount_ht: float
    tva_type: str = "TVA"

class DeadlinesRequest(BaseModel):
    filter_type: Optional[str] = None

class CnpsRequest(BaseModel):
    salaire_brut: float
    nb_employes: int = 1

class TaxSearchRequest(BaseModel):
    query: str

# --- Endpoints MCP ---
@router.post("/tools/convert_currency")
async def tool_convert_currency(req: ConvertCurrencyRequest):
    logger.info("Outil convert_currency: %s %s -> %s", req.amount, req.from_currency, req.to_currency)
    return await convert_currency(req.amount, req.from_currency, req.to_currency)

@router.post("/tools/calculate_vat")
def tool_calculate_vat(req: VatRequest):
    logger.info("Outil calculate_vat: amount_ht=%s tva_type=%s", req.amount_ht, req.tva_type)
    return calculate_vat(req.amount_ht, req.tva_type)

@router.post("/tools/get_tax_deadlines")
def tool_get_tax_deadlines(req: DeadlinesRequest):
    logger.info("Outil get_tax_deadlines: filter_type=%s", req.filter_type)
    return get_tax_deadlines(req.filter_type)

@router.post("/tools/calculate_cnps")
def tool_calculate_cnps(req: CnpsRequest):
    logger.info("Outil calculate_cnps: salaire_brut=%s nb_employes=%s", req.salaire_brut, req.nb_employes)
    return calculate_cnps(req.salaire_brut, req.nb_employes)

@router.post("/tools/search_tax_code")
def tool_search_tax_code(req: TaxSearchRequest):
    logger.info("Outil search_tax_code: query=%s", req.query)
    return search_tax_code(req.query)

@router.get("/tools")
def list_tools():
    return {
        "tools": [
            {"name": "convert_currency",  "description": "Convertit un montant FCFA/EUR/USD/... via taux de change publics"},
            {"name": "calculate_vat",     "description": "Calcule la TVA selon le CGI ivoirien"},
            {"name": "get_tax_deadlines", "description": "Liste les échéances fiscales DGI 2025"},
            {"name": "calculate_cnps",    "description": "Calcule les cotisations CNPS"},
            {"name": "search_tax_code",   "description": "Recherche dans le CGI CI 2025"},
        ]
    }

class ChatRequest(BaseModel):
    messages: list

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    logger.info("Chat: %d message(s) reçu(s)", len(req.messages))
    try:
        return await chat_with_tools(req.messages)
    except Exception as e:
        logger.exception("Erreur lors de l'appel à chat_with_tools")
        raise HTTPException(status_code=502, detail=f"Erreur du service IA: {e}")
