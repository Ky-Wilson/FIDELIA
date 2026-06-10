# Document de décisions d'architecture — FIDELIA

## 1. Vue d'ensemble

FIDELIA est structuré en monorepo avec deux applications indépendantes :

- `backend/` — API FastAPI (Python) : expose les "outils" fiscaux et un endpoint de chat orchestrant ces outils via function-calling LLM.
- `frontend/` — Application React (Vite + Tailwind) : interface de chat consommant l'API backend.

Les deux applications communiquent uniquement via HTTP/JSON, sans état partagé (pas de base de données dans la portée de ce projet — toutes les données fiscales sont des tables de référence statiques).

## 2. Monorepo vs Multi-repo

**Choix : Monorepo** — un seul dépôt Git (`egov-platform/`) avec deux dossiers `frontend/` et `backend/`, une documentation commune (`docs/`) et un `docker-compose.yml` à la racine.

| | Monorepo (choisi) | Multi-repo |
|---|---|---|
| Structure | `egov-platform/` avec `frontend/`, `backend/`, `docs/`, `docker-compose.yml` commun | `egov-frontend` (déploiement Vercel) + `egov-backend` (déploiement Render), 2 dépôts séparés |
| Avantages | Partage de code/config facile, **un seul pipeline CI/CD**, cohérence des configurations, le reviewer voit tout en un coup | Indépendance des équipes, déploiements complètement séparés |
| Inconvénients | Dépôt plus volumineux, permissions moins fines | Configuration dupliquée, deux pipelines CI/CD à maintenir |

**Pourquoi ce choix pour ce projet** : développement en solo, sur un délai court — un monorepo est plus simple à gérer (un seul `git clone`, un seul historique de commits, une seule CI) et facilite l'évaluation (le reviewer accède à frontend, backend et documentation depuis un point unique). Le multi-repo apporterait surtout de la valeur si plusieurs équipes travaillaient indépendamment sur le frontend et le backend avec des cycles de release différents — ce qui n'est pas le cas ici.

Le découplage reste possible malgré le monorepo : `frontend/` et `backend/` ont chacun leur `Dockerfile` et leurs propres dépendances, et peuvent être déployés sur des plateformes différentes (Vercel / Render) sans modification.

## 3. Scalabilité : de 100 à 100 000 utilisateurs

L'architecture actuelle (1 conteneur backend FastAPI + 1 conteneur frontend statique, sans base de données, sans cache) est suffisante pour ~100 utilisateurs simultanés sur un hébergement gratuit. Pour passer à 100 000 utilisateurs, voici comment chaque aspect évoluerait :

- **Stratégie de scaling** : passer d'un seul conteneur à plusieurs réplicas du backend FastAPI derrière un load balancer (ex. Render/Fly.io autoscaling, ou Kubernetes). Le backend est déjà **stateless** (aucune session en mémoire), ce qui rend le scaling horizontal direct — chaque requête peut être traitée par n'importe quelle instance.
- **Caching** :
  - Mettre en cache les réponses de `convert_currency` (taux de change, valides ~1 jour) et de `get_tax_deadlines`/`search_tax_code`/`calculate_vat` (données quasi-statiques) avec Redis, pour réduire les appels API externes et la charge CPU.
  - Cache des réponses LLM pour les questions fréquentes ("Quelles sont les échéances fiscales ?") via un cache sémantique (ex. Redis + recherche par similarité d'embeddings) afin de réduire les coûts OpenAI.
- **Tâches en arrière-plan** : pour des opérations potentiellement longues (ex. génération de DSF complète, traitement de gros volumes de factures FNE), introduire une file de tâches (Celery/RQ + Redis ou Arq) plutôt que de bloquer la requête HTTP.
- **Observabilité** : le logging actuel (`logging` + middleware de requêtes) suffit à 100 utilisateurs. À 100k, il faudrait :
  - centraliser les logs (ex. Grafana Loki, Datadog, ou simplement un service de logs managé du PaaS),
  - ajouter des métriques (latence par endpoint, taux d'erreur, taux d'utilisation par outil) via Prometheus/OpenTelemetry,
  - mettre en place des alertes sur les quotas OpenAI et les erreurs 5xx.
- **Base de données** : actuellement aucune (données fiscales statiques en mémoire). À grande échelle, on introduirait une base (PostgreSQL) pour : historiser les conversations utilisateur, stocker les comptes/authentification, et permettre une mise à jour des barèmes fiscaux (TVA, CNPS, échéances DGI) sans redéploiement — via une table de configuration plutôt que des constantes Python.
- **Coûts** :
  - Le coût dominant à grande échelle serait les appels LLM (cf. [AI_STRATEGY.md](AI_STRATEGY.md)) — le caching sémantique et le choix d'un modèle économique (`gpt-4o-mini` ou équivalent) deviennent critiques.
  - Hébergement : migration des tiers gratuits (Render/Vercel free) vers des plans payants avec autoscaling ; le frontend statique (CDN) scale nativement à coût quasi nul.
  - Le `convert_currency` reste gratuit (`open.er-api.com`) jusqu'à un certain volume — au-delà, prévoir un fournisseur de taux de change payant avec SLA.

Un script de test de montée en charge est fourni dans [`backend/tests/load/locustfile.py`](../backend/tests/load/locustfile.py) pour mesurer le comportement actuel sous charge et identifier le premier goulot d'étranglement (probablement : latence des appels OpenAI, qui sont synchrones par requête de chat).

## 4. "MCP Server" : REST + function-calling plutôt que protocole MCP officiel

Le SDK `mcp` (Model Context Protocol officiel d'Anthropic) est présent dans `requirements.txt` mais **n'est pas utilisé tel quel**. À la place :

- Le backend expose des endpoints REST classiques (`/mcp/tools/{nom_outil}`, `/mcp/chat`) qui jouent le rôle de "serveur d'outils".
- Le endpoint `/mcp/chat` utilise le **function-calling natif d'OpenAI** (`tools` + `tool_choice="auto"`) pour que le LLM décide dynamiquement quel outil appeler, avec les mêmes fonctions Python que les endpoints REST (`execute_tool` dans `chat.py` réutilise les fonctions de `tools/`).

**Justification** :
- Le protocole MCP (transport stdio/SSE, sessions, etc.) est conçu pour connecter un LLM client (ex. Claude Desktop) à un serveur d'outils local. Le besoin ici est une **API web classique consommée par un frontend React** — REST + function-calling reproduit le même principe (description structurée des outils, exécution réelle, retour structuré au LLM) sans la complexité de transport supplémentaire du protocole MCP.
- Le terme "MCP" est conservé dans le nommage (`/mcp/*`, `mcp_server.py`) pour respecter la terminologie de l'énoncé et signaler clairement le rôle de ce module : un serveur d'outils orchestrable par un agent IA.
- **Évolution possible** : le mapping outil → schéma → fonction Python est déjà centralisé (`TOOLS_DEFINITION` + `execute_tool` dans `chat.py`), ce qui faciliterait une migration vers le SDK `mcp` officiel si un client MCP standard (Claude Desktop, etc.) devait consommer ces mêmes outils.

## 5. Choix du LLM : OpenAI (gpt-4o-mini)

- Function-calling mature et stable, format `tools`/`tool_choice` bien documenté.
- `gpt-4o-mini` offre un bon compromis coût/latence/qualité pour un assistant conversationnel avec quelques outils.
- Configurable via `OPENAI_MODEL` sans changement de code.

## 6. Remplacement de `verify_ncc` par `convert_currency`

L'outil `verify_ncc` initialement prévu (vérification d'un Numéro de Compte Contribuable via la plateforme FNE/DGI) appelait un endpoint inexistant. Investigation :

- La documentation officielle FNE ne référence qu'un endpoint `POST /external/invoices/sign`, protégé par un token JWT obtenu après inscription d'entreprise (non disponible pour ce test).
- Aucun endpoint public anonyme de vérification NCC n'a été trouvé (la page `/fr/verification/{token}` est une page web Next.js, pas une API JSON).

**Décision** : remplacer par `convert_currency`, un outil **réel et fonctionnel** s'appuyant sur l'API publique gratuite et sans authentification `open.er-api.com`, pertinent dans le contexte FNE (les factures en devise étrangère, template B2F, nécessitent un taux de conversion).

## 7. Sécurité et observabilité

- **Logging structuré** : `logging` configuré dans `main.py` (format horodaté), middleware HTTP loggant méthode/chemin/statut/durée de chaque requête, et logs applicatifs sur l'exécution des outils (`mcp_server.py`, `chat.py`).
- **Authentification par clé API** : dépendance FastAPI `verify_api_key` (`auth.py`) vérifiant l'en-tête `X-API-Key` contre `MCP_API_KEY`. Désactivée si la variable n'est pas définie (confort de développement). Suffisante pour la portée du projet ; une authentification utilisateur (JWT) serait l'évolution naturelle en production.
- **Gestion d'erreurs** : un handler d'exception global renvoie une réponse JSON `500` propre au lieu d'une trace brute ; les erreurs du endpoint `/mcp/chat` (ex. erreurs OpenAI) sont capturées et renvoyées en `502` avec un message explicite.

## 8. Conteneurisation et CI/CD

- **Backend** : image `python:3.12-slim`, installation des dépendances puis `uvicorn`.
- **Frontend** : build multi-stage (`node:22-alpine` → `nginx:alpine`) servant les fichiers statiques avec gestion du routing SPA (`try_files ... /index.html`).
- **docker-compose.yml** : orchestre les deux services pour un environnement de démonstration local complet.
- **GitHub Actions** (`.github/workflows/ci.yml`) : tests backend (pytest), lint + build frontend, puis build des images Docker — sur chaque push/PR vers `main`.
