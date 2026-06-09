from pydantic import BaseModel
from typing import Literal

TVA_RATES = {
    "TVA":  {"rate": 0.18, "label": "TVA normale 18%"},
    "TVAB": {"rate": 0.09, "label": "TVA réduite 9%"},
    "TVAC": {"rate": 0.00, "label": "TVA exo. conv. 0%"},
    "TVAD": {"rate": 0.00, "label": "TVA exo. légale 0%"},
}

def calculate_vat(amount_ht: float, tva_type: str = "TVA") -> dict:
    """
    Calcule la TVA selon le Code Général des Impôts ivoirien.
    Art. 384 CGI — taux applicables en Côte d'Ivoire.
    """
    tva_type = tva_type.upper()

    if tva_type not in TVA_RATES:
        return {
            "success": False,
            "error": f"Type TVA inconnu: {tva_type}. Valeurs: {list(TVA_RATES.keys())}"
        }

    rate_info = TVA_RATES[tva_type]
    rate = rate_info["rate"]

    tva_amount = round(amount_ht * rate)
    amount_ttc = round(amount_ht + tva_amount)

    return {
        "success": True,
        "tva_type": tva_type,
        "label": rate_info["label"],
        "amount_ht": amount_ht,
        "tva_rate": f"{int(rate * 100)}%",
        "tva_amount": tva_amount,
        "amount_ttc": amount_ttc,
        "currency": "FCFA",
        "source": "CGI Côte d'Ivoire, Art. 384"
    }