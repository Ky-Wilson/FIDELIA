def calculate_cnps(salaire_brut: float, nb_employes: int = 1) -> dict:
    """
    Calcule les cotisations CNPS selon le barème officiel ivoirien.
    Source : Décret CNPS Côte d'Ivoire en vigueur.
    """
    # Taux CNPS Côte d'Ivoire (officiels)
    TAUX_EMPLOYEUR = {
        "retraite":          0.0792,  # 7.92%
        "accidents_travail": 0.02,    # 2% (taux moyen)
        "allocations_fam":   0.055,   # 5.5%
    }
    TAUX_SALARIE = {
        "retraite": 0.036,            # 3.6%
    }
    PLAFOND_MENSUEL = 1_647_315      # FCFA (plafond CNPS 2025)

    base = min(salaire_brut, PLAFOND_MENSUEL)

    part_employeur = sum(taux * base for taux in TAUX_EMPLOYEUR.values())
    part_salarie = sum(taux * base for taux in TAUX_SALARIE.values())
    total_un = part_employeur + part_salarie
    total_all = total_un * nb_employes

    return {
        "success": True,
        "salaire_brut": salaire_brut,
        "base_cotisation": base,
        "plafond_mensuel": PLAFOND_MENSUEL,
        "part_employeur": {
            "retraite":          round(TAUX_EMPLOYEUR["retraite"] * base),
            "accidents_travail": round(TAUX_EMPLOYEUR["accidents_travail"] * base),
            "allocations_fam":   round(TAUX_EMPLOYEUR["allocations_fam"] * base),
            "total":             round(part_employeur),
        },
        "part_salarie": {
            "retraite": round(TAUX_SALARIE["retraite"] * base),
            "total":    round(part_salarie),
        },
        "total_par_employe": round(total_un),
        "nb_employes": nb_employes,
        "total_global": round(total_all),
        "currency": "FCFA",
        "source": "Barème CNPS Côte d'Ivoire 2025"
    }