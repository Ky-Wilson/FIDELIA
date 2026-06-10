# FIDELIA

Assistant fiscal et administratif intelligent pour la Côte d'Ivoire — projet réalisé dans le cadre du test technique "Junior Full Stack Engineer" pour Liwaza (plateforme eGov AI-native).

FIDELIA combine un **serveur d'outils ("MCP server")** exposant des fonctions fiscales (TVA, CNPS, échéances DGI, recherche dans le CGI, conversion de devises) et un **client conversationnel** (chat React) qui orchestre ces outils via function-calling LLM (OpenAI).

## Démo en ligne

- **Frontend** : [fidelia-7jjqaq8eu-ky-wilsons-projects.vercel.app](https://fidelia-7jjqaq8eu-ky-wilsons-projects.vercel.app/)
- **Backend** : [fidelia-76u8.onrender.com](https://fidelia-76u8.onrender.com) (docs interactives sur `/docs`)

> ⚠️ Pour tester le chat (`/mcp/chat`), une clé API OpenAI doit être renseignée dans les variables d'environnement du service Render (`OPENAI_API_KEY`) — voir [Variables d'environnement](#variables-denvironnement). Sans clé, l'app reste pleinement accessible et les outils `/mcp/tools/*` fonctionnent normalement, mais le chat affiche un message invitant à configurer la clé. Le backend Render (plan gratuit) peut mettre quelques dizaines de secondes à se réveiller après une période d'inactivité.

## Sommaire

- [Démo en ligne](#démo-en-ligne)
- [Architecture](#architecture)
- [Outils MCP disponibles](#outils-mcp-disponibles)
- [Démarrage rapide (Docker)](#démarrage-rapide-docker)
- [Démarrage en local (sans Docker)](#démarrage-en-local-sans-docker)
- [Variables d'environnement](#variables-denvironnement)
- [Tests](#tests)
- [Documentation complémentaire](#documentation-complémentaire)
- [Choix techniques et tradeoffs](#choix-techniques-et-tradeoffs)
- [Déploiement](#déploiement)
- [Hypothèses, limites connues et améliorations futures](#hypothèses-limites-connues-et-améliorations-futures)

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

> Ce dépôt est organisé en **monorepo** (un seul dépôt pour `frontend/` et `backend/`). Voir [docs/ARCHITECTURE.md §2](docs/ARCHITECTURE.md#2-monorepo-vs-multi-repo) pour la justification de ce choix face à une organisation multi-repo.

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
| `OPENAI_API_KEY` | non* | — | Clé API OpenAI utilisée pour le chat avec function-calling. *L'app démarre sans, mais `/mcp/chat` répond `502` tant qu'elle n'est pas définie — les autres outils (`/mcp/tools/*`) fonctionnent normalement. |
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

### Ce qui est testé, ce qui ne l'est pas, et pourquoi

| Couvert ✅ | Non couvert ⚠️ | Pourquoi |
|---|---|---|
| Calculs fiscaux (`calculate_vat`, `calculate_cnps`) — tous les taux/cas | Le frontend React (pas de tests Vitest/RTL) | Priorité donnée au backend (cœur métier + bug à corriger) ; le frontend a été vérifié manuellement (lint, build, usage dans le navigateur) |
| `convert_currency` — succès, devise inconnue, erreur HTTP (mocké avec `respx`) | Appel réel à OpenAI (`/mcp/chat` avec une vraie clé API) | Aucune clé OpenAI valide disponible pendant le développement ; le endpoint est testé avec `chat_with_tools` mocké (`AsyncMock`) pour valider le contrat HTTP/JSON |
| `get_tax_deadlines`, `search_tax_code` — filtres et recherche | Tests de charge automatisés en CI | Le scénario Locust (ci-dessous) est fourni mais s'exécute manuellement — l'intégrer en CI nécessiterait un environnement dédié et une vraie clé OpenAI |
| Endpoints REST (`/`, `/health`, `/mcp/tools/*`, `/mcp/chat`) — succès et erreurs | Authentification par clé API : tous les endpoints `/mcp/*` avec/sans `X-API-Key` | Comportement vérifié, jugé suffisant pour la portée du test |

### Tests de montée en charge

Un scénario [Locust](https://locust.io) est fourni dans [`backend/tests/load/locustfile.py`](backend/tests/load/locustfile.py) pour évaluer le comportement du backend sous charge (endpoints "outils" déterministes vs `/mcp/chat`, qui dépend de la latence OpenAI) :

```bash
cd backend
source venv/bin/activate
pip install -r requirements-dev.txt

uvicorn main:app --port 8000 &
locust -f tests/load/locustfile.py --host http://localhost:8000
```

Puis ouvrir http://localhost:8089 pour piloter le test (nombre d'utilisateurs simulés, taux de spawn) et observer la latence / le taux d'erreur. Voir [docs/ARCHITECTURE.md §3](docs/ARCHITECTURE.md#3-scalabilité--de-100-à-100-000-utilisateurs) pour l'analyse de scalabilité associée.

## Documentation complémentaire

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — décisions d'architecture (choix techniques, MCP vs REST, etc.)
- [docs/AI_STRATEGY.md](docs/AI_STRATEGY.md) — stratégie d'intégration LLM / function-calling

## Choix techniques et tradeoffs

Résumé des principaux arbitrages effectués (détails et alternatives envisagées dans `docs/`) :

| Choix | Alternative envisagée | Pourquoi ce choix | Détails |
|---|---|---|---|
| Monorepo (`frontend/` + `backend/` + `docs/`) | Multi-repo (2 dépôts séparés) | Projet solo, délai court, évaluation facilitée par un point d'accès unique ; le découplage de déploiement reste possible (Dockerfiles séparés) | [ARCHITECTURE.md §2](docs/ARCHITECTURE.md#2-monorepo-vs-multi-repo) |
| REST + function-calling OpenAI plutôt que SDK `mcp` officiel | Implémenter le protocole MCP (stdio/SSE) | Le besoin réel est une API web consommée par un frontend React ; REST + function-calling reproduit le même principe sans la complexité de transport du protocole MCP | [ARCHITECTURE.md §4](docs/ARCHITECTURE.md#4-mcp-server--rest--function-calling-plutôt-que-protocole-mcp-officiel) |
| OpenAI `gpt-4o-mini` | Claude, Gemini, Llama, Mistral | Function-calling jugé le plus robuste par le développeur + seule clé API disponible pendant le développement ; migration possible sans changer la logique métier | [AI_STRATEGY.md §2-3](docs/AI_STRATEGY.md#2-comparatif-des-modèles-disponibles-sur-le-marché-2026) |
| `convert_currency` (API publique réelle) à la place de `verify_ncc` | Mock/stub de `verify_ncc` | L'énoncé exige une exécution d'outil réelle ("no fake responses") ; aucun endpoint NCC public n'existe, alors qu'`open.er-api.com` est réel, gratuit et pertinent pour le contexte FNE | [ARCHITECTURE.md §6](docs/ARCHITECTURE.md#6-remplacement-de-verify_ncc-par-convert_currency) |
| Auth simple par clé API (`X-API-Key`) | Auth utilisateur (JWT, comptes) | Suffisant pour la portée du test (protéger un proxy LLM) ; une auth utilisateur serait l'évolution naturelle pour la production | [ARCHITECTURE.md §7](docs/ARCHITECTURE.md#7-sécurité-et-observabilité) |
| Données fiscales codées en dur (TVA, CNPS, échéances, CGI) | Base de données / API externe | Données de référence légales peu volatiles ; évite une dépendance DB pour un projet de cette taille | [README — Hypothèses](#hypothèses-limites-connues-et-améliorations-futures) |

## Déploiement

Le projet est déployé sur des plateformes gratuites (voir [Démo en ligne](#démo-en-ligne)). Voici la procédure suivie, utile pour répliquer le déploiement ou en créer un nouveau.

### Backend (Render)

1. Pousser le repo sur GitHub.
2. Sur [Render](https://render.com), créer un **Web Service** depuis le repo, dossier racine `backend/`.
3. Render détecte le `Dockerfile` (ou définir manuellement : build `pip install -r requirements.txt`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`).
4. Renseigner les variables d'environnement : `OPENAI_API_KEY` (à fournir par le testeur), `OPENAI_MODEL`, `APP_ENV=production`, `MCP_API_KEY` (optionnel).
5. Une fois déployé, noter l'URL publique (ici : `https://fidelia-76u8.onrender.com`).

Alternatives équivalentes : Railway, Fly.io (toutes supportent un déploiement direct depuis le `Dockerfile` du dossier `backend/`).

### Frontend (Vercel)

1. Sur [Vercel](https://vercel.com), importer le repo. Comme c'est un monorepo, **régler Root Directory = `frontend`** (preset Vite détecté automatiquement).
2. Renseigner la variable d'environnement `VITE_API_URL` avec l'URL du backend déployé (ici : `https://fidelia-76u8.onrender.com`).
3. Déployer — build command `npm run build`, output `dist/`.
4. CORS : `backend/main.py` autorise déjà tous les sous-domaines `*.vercel.app` via `allow_origin_regex` — aucune modification nécessaire si le domaine change (preview deployments inclus).

## Hypothèses, limites connues et améliorations futures

### Hypothèses et limites connues

- **`verify_ncc` remplacé par `convert_currency`** : l'outil initialement prévu pour vérifier un NCC via l'API FNE/DGI nécessite des identifiants d'entreprise (JWT Bearer obtenu après inscription) qui ne sont pas disponibles pour ce test. Aucun endpoint public anonyme de vérification NCC n'existe. Il a été remplacé par un outil de conversion de devises réel et fonctionnel (utile pour les factures FNE en devise étrangère, template B2F), s'appuyant sur l'API publique gratuite `open.er-api.com`.
- **Authentification** : une authentification simple par clé API (`X-API-Key`) est disponible et désactivable via `MCP_API_KEY` — suffisante pour la portée de ce projet. Une authentification utilisateur (JWT/comptes) serait l'évolution naturelle pour une mise en production.
- **Données fiscales** (TVA, CNPS, échéances, CGI) : tables officielles codées en dur dans les outils — il ne s'agit pas de "réponses fake" mais de données de référence légales, peu sujettes à changement fréquent.

### Améliorations futures

- **Mise à jour des barèmes fiscaux sans redéploiement** : déplacer les tables TVA/CNPS/échéances/CGI vers une base de données ou un fichier de configuration externe, modifiable sans changer le code.
- **Authentification utilisateur** : remplacer/compléter `MCP_API_KEY` par une authentification par compte (JWT), avec historique de conversation par utilisateur.
- **Cache (Redis)** : mettre en cache les taux de change (`convert_currency`, valides ~1 jour) et les réponses LLM aux questions fréquentes (cache sémantique), pour réduire la latence et les coûts OpenAI — voir [ARCHITECTURE.md §3](docs/ARCHITECTURE.md#3-scalabilité--de-100-à-100-000-utilisateurs).
- **Observabilité avancée** : centralisation des logs et métriques (Prometheus/OpenTelemetry, Grafana) pour le suivi en production.
- **Tests frontend** : ajouter des tests Vitest/React Testing Library pour les composants `Chat.jsx` et `ToolResult.jsx`.
- **CI pour les tests de charge** : intégrer le scénario Locust dans un job CI dédié (avec une clé OpenAI de test) pour détecter les régressions de performance.
- **Multi-provider LLM** : abstraire l'appel LLM (`chat.py`) pour permettre de basculer entre OpenAI, Claude, Gemini ou un modèle auto-hébergé selon le contexte (coût, confidentialité) — voir [AI_STRATEGY.md §4](docs/AI_STRATEGY.md#4-confidentialité-sécurité-et-conformité-rgpd--souveraineté-des-données).
