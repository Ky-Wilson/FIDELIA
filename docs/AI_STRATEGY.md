# Stratégie IA / LLM — FIDELIA

## 1. Modèle et provider

- **Provider** : OpenAI, via le SDK officiel `openai` (client `AsyncOpenAI`).
- **Modèle** : `gpt-4o-mini` par défaut (configurable via `OPENAI_MODEL`).
- **Pourquoi** : function-calling natif robuste, latence/coût adaptés à un assistant conversationnel avec un nombre réduit d'outils, et large documentation.

## 2. Orchestration : function-calling, pas de framework d'agents

Le endpoint `/mcp/chat` (`backend/chat.py`) implémente un cycle d'orchestration en 2 appels :

1. **Premier appel** : le modèle reçoit l'historique de conversation + le `SYSTEM_PROMPT` (contexte FIDELIA, ton, langues FR/EN) + la liste `TOOLS_DEFINITION` (schémas JSON des 5 outils), avec `tool_choice="auto"`.
2. Si le modèle choisit d'appeler un outil (`message.tool_calls`), le backend :
   - parse les arguments JSON générés par le modèle,
   - exécute la **fonction Python réelle correspondante** (`execute_tool`), qui appelle soit un calcul fiscal local, soit l'API publique de taux de change,
   - renvoie le résultat de l'outil au modèle dans un **second appel** (rôle `tool`), pour que le modèle formule une réponse en langage naturel intégrant ce résultat.
3. La réponse finale (`text`), l'outil utilisé (`tool_used`) et ses données brutes (`tool_data`) sont renvoyés au frontend, qui affiche à la fois le texte et un composant de visualisation dédié (`ToolResult.jsx`) selon l'outil.

**Pourquoi pas un framework d'agents (LangChain, CrewAI, etc.)** : avec seulement 5 outils déterministes et un seul tour d'appel d'outil par message, le function-calling natif d'OpenAI couvre le besoin sans dépendance supplémentaire ni complexité d'abstraction. Un framework deviendrait pertinent si le nombre d'outils augmentait significativement, si des chaînes d'outils multi-étapes étaient nécessaires, ou si plusieurs providers LLM devaient être interchangeables dynamiquement.

## 3. Prompt système

Le `SYSTEM_PROMPT` (en français) cadre :
- l'identité de l'assistant (FIDELIA, assistant fiscal CI),
- le périmètre fonctionnel (FNE/DGI, TVA, échéances, CNPS, CGI),
- le bilinguisme FR/EN selon la langue de l'utilisateur,
- le ton (précis, professionnel, bienveillant),
- la consigne d'expliquer brièvement le résultat d'un outil après son exécution.

## 4. Garantie "pas de réponses fake"

Conformément à l'exigence du test ("Tool execution must be real"), chaque outil exécute un traitement réel :

- `convert_currency` : appel HTTP réel vers `open.er-api.com` (taux de change publics, mis à jour quotidiennement) — voir [docs/ARCHITECTURE.md](ARCHITECTURE.md) pour la justification du remplacement de `verify_ncc`.
- `calculate_vat`, `calculate_cnps`, `get_tax_deadlines`, `search_tax_code` : calculs/recherches déterministes sur des tables de référence officielles (CGI, barèmes CNPS, calendrier DGI) — pas de réponses statiques générées par le LLM.

Le LLM ne fait **que** : (1) choisir l'outil et ses paramètres, (2) reformuler le résultat en langage naturel. Il ne génère jamais lui-même les chiffres/résultats fiscaux.

## 5. Gestion des erreurs et résilience

- Les erreurs de l'API OpenAI (quota, authentification, timeout) sont capturées dans `mcp_server.py` et renvoyées au frontend sous forme de `502 Bad Gateway` avec un message explicite, plutôt qu'un `500` générique.
- Les erreurs de l'API de taux de change (`convert_currency`) sont gérées explicitement (timeout, devise inconnue, erreur HTTP) et retournées sous forme de `{"success": false, "error": "..."}`, que le LLM peut alors expliquer à l'utilisateur.

## 6. Sécurité

- La clé `OPENAI_API_KEY` n'est utilisée que côté backend ; elle n'est **jamais exposée au navigateur** (le frontend appelle uniquement l'API FastAPI, qui elle-même appelle OpenAI).
- Le endpoint `/mcp/chat` peut être protégé par une clé API applicative (`MCP_API_KEY` / en-tête `X-API-Key`), indépendante de la clé OpenAI, pour limiter l'usage du proxy de chat.

## 7. Utilisation de l'IA pendant le développement de ce projet

Conformément à la politique d'usage de l'IA de l'évaluation : un assistant IA (Claude Code) a été utilisé pour accélérer le diagnostic d'erreurs (tracebacks FastAPI/Pydantic/OpenAI), la rédaction de code répétitif (endpoints CRUD-like, tests, Dockerfiles), et la rédaction de cette documentation. Les décisions d'architecture (choix d'API de remplacement, structure d'authentification, stratégie de tests) ont été validées itérativement avec le développeur.
