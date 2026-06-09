# Document de décisions d'architecture — FIDELIA

## 1. Vue d'ensemble

FIDELIA est structuré en monorepo avec deux applications indépendantes :

- `backend/` — API FastAPI (Python) : expose les "outils" fiscaux et un endpoint de chat orchestrant ces outils via function-calling LLM.
- `frontend/` — Application React (Vite + Tailwind) : interface de chat consommant l'API backend.

Les deux applications communiquent uniquement via HTTP/JSON, sans état partagé (pas de base de données dans la portée de ce projet — toutes les données fiscales sont des tables de référence statiques).

## 2. Pourquoi un monorepo ?

- **Cohérence de version** : backend et frontend évoluent ensemble pour ce produit unique ; un monorepo évite la synchronisation de plusieurs dépôts pour un projet de cette taille.
- **CI/CD unique** : un seul workflow GitHub Actions peut tester/builder les deux projets.
- **Simplicité pour un test technique** : un seul `git clone` donne accès à l'ensemble du contexte.

Inconvénient assumé : déploiements backend/frontend non strictement découplés (mitigé par des Dockerfiles et pipelines de build séparés par dossier).

## 3. "MCP Server" : REST + function-calling plutôt que protocole MCP officiel

Le SDK `mcp` (Model Context Protocol officiel d'Anthropic) est présent dans `requirements.txt` mais **n'est pas utilisé tel quel**. À la place :

- Le backend expose des endpoints REST classiques (`/mcp/tools/{nom_outil}`, `/mcp/chat`) qui jouent le rôle de "serveur d'outils".
- Le endpoint `/mcp/chat` utilise le **function-calling natif d'OpenAI** (`tools` + `tool_choice="auto"`) pour que le LLM décide dynamiquement quel outil appeler, avec les mêmes fonctions Python que les endpoints REST (`execute_tool` dans `chat.py` réutilise les fonctions de `tools/`).

**Justification** :
- Le protocole MCP (transport stdio/SSE, sessions, etc.) est conçu pour connecter un LLM client (ex. Claude Desktop) à un serveur d'outils local. Le besoin ici est une **API web classique consommée par un frontend React** — REST + function-calling reproduit le même principe (description structurée des outils, exécution réelle, retour structuré au LLM) sans la complexité de transport supplémentaire du protocole MCP.
- Le terme "MCP" est conservé dans le nommage (`/mcp/*`, `mcp_server.py`) pour respecter la terminologie de l'énoncé et signaler clairement le rôle de ce module : un serveur d'outils orchestrable par un agent IA.
- **Évolution possible** : le mapping outil → schéma → fonction Python est déjà centralisé (`TOOLS_DEFINITION` + `execute_tool` dans `chat.py`), ce qui faciliterait une migration vers le SDK `mcp` officiel si un client MCP standard (Claude Desktop, etc.) devait consommer ces mêmes outils.

## 4. Choix du LLM : OpenAI (gpt-4o-mini)

- Function-calling mature et stable, format `tools`/`tool_choice` bien documenté.
- `gpt-4o-mini` offre un bon compromis coût/latence/qualité pour un assistant conversationnel avec quelques outils.
- Configurable via `OPENAI_MODEL` sans changement de code.

## 5. Remplacement de `verify_ncc` par `convert_currency`

L'outil `verify_ncc` initialement prévu (vérification d'un Numéro de Compte Contribuable via la plateforme FNE/DGI) appelait un endpoint inexistant. Investigation :

- La documentation officielle FNE ne référence qu'un endpoint `POST /external/invoices/sign`, protégé par un token JWT obtenu après inscription d'entreprise (non disponible pour ce test).
- Aucun endpoint public anonyme de vérification NCC n'a été trouvé (la page `/fr/verification/{token}` est une page web Next.js, pas une API JSON).

**Décision** : remplacer par `convert_currency`, un outil **réel et fonctionnel** s'appuyant sur l'API publique gratuite et sans authentification `open.er-api.com`, pertinent dans le contexte FNE (les factures en devise étrangère, template B2F, nécessitent un taux de conversion).

## 6. Sécurité et observabilité

- **Logging structuré** : `logging` configuré dans `main.py` (format horodaté), middleware HTTP loggant méthode/chemin/statut/durée de chaque requête, et logs applicatifs sur l'exécution des outils (`mcp_server.py`, `chat.py`).
- **Authentification par clé API** : dépendance FastAPI `verify_api_key` (`auth.py`) vérifiant l'en-tête `X-API-Key` contre `MCP_API_KEY`. Désactivée si la variable n'est pas définie (confort de développement). Suffisante pour la portée du projet ; une authentification utilisateur (JWT) serait l'évolution naturelle en production.
- **Gestion d'erreurs** : un handler d'exception global renvoie une réponse JSON `500` propre au lieu d'une trace brute ; les erreurs du endpoint `/mcp/chat` (ex. erreurs OpenAI) sont capturées et renvoyées en `502` avec un message explicite.

## 7. Conteneurisation et CI/CD

- **Backend** : image `python:3.12-slim`, installation des dépendances puis `uvicorn`.
- **Frontend** : build multi-stage (`node:22-alpine` → `nginx:alpine`) servant les fichiers statiques avec gestion du routing SPA (`try_files ... /index.html`).
- **docker-compose.yml** : orchestre les deux services pour un environnement de démonstration local complet.
- **GitHub Actions** (`.github/workflows/ci.yml`) : tests backend (pytest), lint + build frontend, puis build des images Docker — sur chaque push/PR vers `main`.
