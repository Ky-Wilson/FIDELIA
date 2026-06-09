CGI_ARTICLES = [
    {"article": "Art. 384", "titre": "Obligation de facturation normalisée (FNE)", "texte": "Toute entreprise assujettie doit émettre une Facture Normalisée Électronique certifiée par la DGI via la plateforme FNE.", "categorie": "TVA"},
    {"article": "Art. 356", "titre": "Taux normal de TVA", "texte": "Le taux normal de la taxe sur la valeur ajoutée est fixé à 18% du prix hors taxe.", "categorie": "TVA"},
    {"article": "Art. 357", "titre": "Taux réduit de TVA", "texte": "Un taux réduit de 9% s'applique à certains produits de grande consommation définis par arrêté.", "categorie": "TVA"},
    {"article": "Art. 24",  "titre": "Impôt sur les sociétés — taux", "texte": "Le taux de l'impôt sur les bénéfices des sociétés est fixé à 25% du bénéfice imposable.", "categorie": "IS"},
    {"article": "Art. 61",  "titre": "Acomptes provisionnels IS", "texte": "Les sociétés versent quatre acomptes trimestriels égaux à 25% de l'impôt de l'exercice précédent.", "categorie": "IS"},
    {"article": "Art. 116", "titre": "Patente — base d'imposition", "texte": "La patente est établie sur la valeur locative des locaux professionnels et le chiffre d'affaires.", "categorie": "Patente"},
    {"article": "Art. 903", "titre": "Déclaration statistique et fiscale (DSF)", "texte": "Toute entreprise doit déposer une DSF avant le 31 mars de chaque année auprès de la DGI.", "categorie": "DSF"},
]

def search_tax_code(query: str) -> dict:
    """
    Recherche dans le Code Général des Impôts de Côte d'Ivoire.
    Source : CGI CI édition 2025 — dgi.cgici.com
    """
    query_lower = query.lower()
    results = []

    for article in CGI_ARTICLES:
        score = 0
        if query_lower in article["titre"].lower():
            score += 3
        if query_lower in article["texte"].lower():
            score += 2
        if query_lower in article["categorie"].lower():
            score += 1
        if query_lower in article["article"].lower():
            score += 2
        if score > 0:
            results.append({**article, "pertinence": score})

    results.sort(key=lambda x: x["pertinence"], reverse=True)

    return {
        "success": True,
        "query": query,
        "total": len(results),
        "results": results,
        "source": "Code Général des Impôts CI — Édition 2025"
    }