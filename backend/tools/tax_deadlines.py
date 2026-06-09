from datetime import date

TAX_DEADLINES_2025 = [
    {"nom": "TVA mensuelle (mai)",    "date": "2025-06-20", "type": "TVA",   "frequence": "mensuelle"},
    {"nom": "TVA mensuelle (juin)",   "date": "2025-07-20", "type": "TVA",   "frequence": "mensuelle"},
    {"nom": "Acompte IS T2",          "date": "2025-06-30", "type": "IS",    "frequence": "trimestrielle"},
    {"nom": "CNPS déclaration T2",    "date": "2025-07-15", "type": "CNPS",  "frequence": "trimestrielle"},
    {"nom": "Patente annuelle",       "date": "2025-07-31", "type": "Patente","frequence": "annuelle"},
    {"nom": "TVA mensuelle (juillet)","date": "2025-08-20", "type": "TVA",   "frequence": "mensuelle"},
    {"nom": "Acompte IS T3",          "date": "2025-09-30", "type": "IS",    "frequence": "trimestrielle"},
    {"nom": "CNPS déclaration T3",    "date": "2025-10-15", "type": "CNPS",  "frequence": "trimestrielle"},
    {"nom": "DSF annuelle",           "date": "2025-03-31", "type": "DSF",   "frequence": "annuelle"},
]

def get_tax_deadlines(filter_type: str = None) -> dict:
    """
    Retourne les échéances fiscales DGI Côte d'Ivoire pour 2025.
    Source : Calendrier fiscal DGI publié annuellement.
    """
    today = date.today()
    deadlines = TAX_DEADLINES_2025

    if filter_type:
        deadlines = [d for d in deadlines if d["type"].upper() == filter_type.upper()]

    upcoming = []
    for d in deadlines:
        deadline_date = date.fromisoformat(d["date"])
        days_remaining = (deadline_date - today).days
        upcoming.append({
            **d,
            "jours_restants": days_remaining,
            "statut": "passé" if days_remaining < 0 else "urgent" if days_remaining <= 7 else "à venir"
        })

    upcoming.sort(key=lambda x: x["date"])

    return {
        "success": True,
        "total": len(upcoming),
        "echeances": upcoming,
        "source": "Calendrier fiscal DGI CI 2025"
    }