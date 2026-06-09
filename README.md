# FIDELIA

Assistant fiscal et administratif intelligent pour la Côte d'Ivoire — projet réalisé dans le cadre du test technique "Junior Full Stack Engineer" pour Liwaza (plateforme eGov AI-native).

FIDELIA combine un **serveur d'outils ("MCP server")** exposant des fonctions fiscales (TVA, CNPS, échéances DGI, recherche dans le CGI, conversion de devises) et un **client conversationnel** (chat React) qui orchestre ces outils via function-calling LLM (OpenAI).

## Sommaire

- [Architecture](#architecture)
- [Outils MCP disponibles](#outils-mcp-disponibles)
- [Démarrage rapide (Docker)](#démarrage-rapide-docker)
- [Démarrage en local (sans Docker)](#démarrage-en-local-sans-docker)
- [Variables d'environnement](#variables-denvironnement)
- [Tests](#tests)
- [Documentation complémentaire](#documentation-complémentaire)
- [Hypothèses et limites connues](#hypothèses-et-limites-connues)

## Architecture

```text
┌─────────────────┐        HTTP/JSON        ┌──────────────────────┐
│  Frontend React  │ ───────────────────────▶│   Backend FastAPI     │
│  (Vite + Tailwind)│ ◀─────────────────────── │   "MCP server"        │
│  /mcp/chat        │                          │  - /mcp/chat          │
│  /mcp/tools/*     │                          │  - /mcp/tools/*       │
└─────────────────┘                          └──────────┬───────────┘
                                                          │
                                          ┌───────────────┼────────────────┐
                                          ▼               ▼                ▼
                                   OpenAI API     open.er-api.com    Données fiscales
                                  (function-calling) (taux de change)  CI (CGI, CNPS, DGI)
```

- **Backend** (`backend/`) : API FastAPI exposant 5 outils fiscaux + un endpoint de chat qui utilise le function-calling OpenAI pour décider quel outil appeler.
- **Frontend** (`frontend/`) : interface de chat React/Vite/Tailwind, consomme l'API backend.

## Outils MCP disponibles

| Outil | Description | Source des données |
|---|---|---|
| `convert_currency` | Convertit un montant entre devises (XOF/FCFA, EUR, USD, ...) | API publique gratuite [open.er-api.com](https://open.er-api.com) (taux de change réels) |
| `calculate_vat` | Calcule la TVA (18% / 9% / 0%) selon le CGI ivoirien | Code Général des Impôts CI, Art. 384 |
| `get_tax_deadlines` | Liste les échéances fiscales DGI 2025 | Calendrier fiscal DGI CI |
| `calculate_cnps` | Calcule les cotisations CNPS (employeur/salarié) | Barème CNPS Côte d'Ivoire 2025 |
| `search_tax_code` | Recherche dans le Code Général des Impôts CI | CGI CI édition 2025 |

## Démarrage rapide (Docker)

Prérequis : Docker + Docker Compose.

```bash
cp .env.example .env
# éditer .env et renseigner OPENAI_API_KEY

docker compose up --build
```

- Backend : http://localhost:8000 (docs interactives sur `/docs`)
- Frontend : http://localhost:5173

## Démarrage en local (sans Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # ou créer backend/.env directement
# renseigner OPENAI_API_KEY dans backend/.env

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend disponible sur http://localhost:5173, configuré pour appeler le backend sur `http://localhost:8000` (variable `VITE_API_URL`).

## Variables d'environnement

### Backend (`backend/.env`)

| Variable | Obligatoire | Défaut | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | oui | — | Clé API OpenAI utilisée pour le chat avec function-calling |
| `OPENAI_MODEL` | non | `gpt-4o-mini` | Modèle OpenAI utilisé |
| `APP_ENV` | non | `development` | Environnement (`development` / `production`) |
| `MCP_API_KEY` | non | _(désactivé)_ | Si défini, les endpoints `/mcp/*` exigent l'en-tête `X-API-Key` correspondant |

### Frontend (`frontend/.env`)

| Variable | Défaut | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | URL du backend FastAPI |

Voir [.env.example](.env.example) à la racine pour un modèle complet.

## Tests

```bash
cd backend
source venv/bin/activate
pip install -r requirements-dev.txt
pytest -v
```

Couverture : tests unitaires pour les 5 outils (calculs fiscaux + appel API de conversion mocké avec `respx`) et tests d'intégration sur les endpoints FastAPI (`/`, `/health`, `/mcp/tools/*`, `/mcp/chat`, authentification par clé API).

## Documentation complémentaire

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — décisions d'architecture (choix techniques, MCP vs REST, etc.)
- [docs/AI_STRATEGY.md](docs/AI_STRATEGY.md) — stratégie d'intégration LLM / function-calling

## Déploiement (guide)

Le projet est conteneurisé et prêt à déployer sur des plateformes gratuites. N'a pas été déployé dans le cadre de ce test (pas d'accès aux comptes d'hébergement de l'évaluateur) ; voici la procédure recommandée.

### Backend (Render)

1. Pousser le repo sur GitHub.
2. Sur [Render](https://render.com), créer un **Web Service** depuis le repo, dossier racine `backend/`.
3. Render détecte le `Dockerfile` (ou définir manuellement : build `pip install -r requirements.txt`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`).
4. Renseigner les variables d'environnement : `OPENAI_API_KEY`, `OPENAI_MODEL`, `APP_ENV=production`, `MCP_API_KEY` (optionnel).
5. Une fois déployé, noter l'URL publique (ex. `https://fidelia-backend.onrender.com`).

Alternatives équivalentes : Railway, Fly.io (toutes supportent un déploiement direct depuis le `Dockerfile` du dossier `backend/`).

### Frontend (Vercel)

1. Sur [Vercel](https://vercel.com), importer le repo, dossier racine `frontend/` (preset Vite détecté automatiquement).
2. Renseigner la variable d'environnement `VITE_API_URL` avec l'URL du backend déployé (ex. `https://fidelia-backend.onrender.com`).
3. Déployer — build command `npm run build`, output `dist/`.
4. Mettre à jour `allow_origins` dans `backend/main.py` si le domaine Vercel diffère de `*.vercel.app`.

## Hypothèses et limites connues

- **`verify_ncc` remplacé par `convert_currency`** : l'outil initialement prévu pour vérifier un NCC via l'API FNE/DGI nécessite des identifiants d'entreprise (JWT Bearer obtenu après inscription) qui ne sont pas disponibles pour ce test. Aucun endpoint public anonyme de vérification NCC n'existe. Il a été remplacé par un outil de conversion de devises réel et fonctionnel (utile pour les factures FNE en devise étrangère, template B2F), s'appuyant sur l'API publique gratuite `open.er-api.com`.
- **Authentification** : une authentification simple par clé API (`X-API-Key`) est disponible et désactivable via `MCP_API_KEY` — suffisante pour la portée de ce projet. Une authentification utilisateur (JWT/comptes) serait l'évolution naturelle pour une mise en production.
- **Données fiscales** (TVA, CNPS, échéances, CGI) : tables officielles codées en dur dans les outils — il ne s'agit pas de "réponses fake" mais de données de référence légales, peu sujettes à changement fréquent.
