# Stratégie IA / LLM — FIDELIA

## 1. Modèle et provider

- **Provider** : OpenAI, via le SDK officiel `openai` (client `AsyncOpenAI`).
- **Modèle** : `gpt-4o-mini` par défaut (configurable via `OPENAI_MODEL`).
- **Pourquoi** : function-calling natif robuste, latence/coût adaptés à un assistant conversationnel avec un nombre réduit d'outils, et large documentation.

## 2. Comparatif des modèles disponibles sur le marché (2026)

L'énoncé du test mentionne plusieurs familles de modèles (OpenAI, Anthropic, Google, Llama, Mistral). Voici un comparatif des offres pertinentes pour un cas d'usage de **function-calling conversationnel léger** (quelques outils, prompts courts à moyens), avec des ordres de grandeur de coût et de positionnement par domaine d'usage.

### Coûts indicatifs (par million de tokens, USD)

| Modèle | Input | Output | Fenêtre de contexte | Remarque |
|---|---|---|---|---|
| **OpenAI GPT-4.1** | ~2,00 $ | ~8,00 $ | 1M tokens | Raisonnement et code très solides, bon function-calling |
| **OpenAI GPT-4o** | ~2,50 $ | ~10,00 $ | 128k tokens | Multimodal, bon généraliste |
| **OpenAI GPT-4o-mini** | ~0,15 $ | ~0,60 $ | 128k tokens | Très bon rapport qualité/prix, function-calling fiable |
| **Anthropic Claude Opus 4** | ~15,00 $ | ~75,00 $ | 200k tokens | Le plus puissant pour le raisonnement long/complexe, coût élevé |
| **Anthropic Claude Sonnet 4** | ~3,00 $ | ~15,00 $ | 200k tokens | Excellent compromis raisonnement/coût, très bon en code |
| **Anthropic Claude Haiku** | ~0,80 $ | ~4,00 $ | 200k tokens | Rapide et économique, adapté aux tâches simples |
| **Google Gemini 2.5 Pro** | ~1,25 $ | ~10,00 $ | 1M+ tokens | Très grande fenêtre de contexte, bon en multimodal |
| **Google Gemini 2.5 Flash** | ~0,30 $ | ~2,50 $ | 1M tokens | Rapide, économique, bon pour des tâches structurées |
| **Meta Llama 4 (via Together AI / Groq / etc.)** | ~0,20 – 0,60 $ | ~0,60 – 1,20 $ | 128k–10M tokens (selon variante) | Open-weight, **auto-hébergeable**, pas de dépendance à un provider tiers |
| **Mistral Small / Medium** | ~0,10 – 0,40 $ | ~0,30 – 2,00 $ | 32k–128k | Modèles européens, open-weight pour certaines variantes, conformité RGPD facilitée |

> Ces tarifs évoluent fréquemment et sont donnés à titre indicatif (ordres de grandeur début 2026) ; ils servent à comparer les **familles de coûts relatifs** plutôt qu'à fournir un devis exact.

### Performance par domaine d'usage

- **Raisonnement complexe / multi-étapes** (ex. analyse fiscale fine, enchaînement de plusieurs outils, explication de cas limites du CGI) : Claude Opus/Sonnet et GPT-4.1 sont historiquement en tête sur les benchmarks de raisonnement et de suivi d'instructions strictes ; Gemini 2.5 Pro est compétitif notamment grâce à sa fenêtre de contexte.
- **Function-calling / structuration JSON** : GPT-4o/4o-mini et Claude Sonnet ont un format `tools` mature, bien documenté, avec un taux d'erreur de parsing faible — c'est le critère le plus important pour FIDELIA, où chaque message peut déclencher un appel d'outil.
- **Coût à grande échelle (100k+ utilisateurs)** : GPT-4o-mini, Gemini 2.5 Flash et Mistral Small dominent largement sur le rapport coût/qualité pour des conversations courtes et des appels d'outils répétitifs.
- **Multilingue (FR/EN, contexte ivoirien)** : GPT-4o(-mini), Claude Sonnet et Gemini 2.5 ont tous un excellent support du français ; peu de différenciation pratique sur ce critère pour ce projet.
- **Auto-hébergement / souveraineté des données** : Llama 4 et Mistral (modèles open-weight) sont les seules options permettant un déploiement on-premise ou chez un hébergeur souverain, pertinent pour une plateforme eGov manipulant des données fiscales sensibles.

## 3. Justification du choix : OpenAI (`gpt-4o-mini`)

Le choix d'OpenAI pour ce projet repose sur **deux raisons concrètes** :

1. **Robustesse perçue en raisonnement et en function-calling** : dans l'expérience du développeur, les modèles OpenAI (GPT-4o et la famille GPT-4.1) offrent le comportement le plus fiable et le plus prévisible pour le function-calling — c'est-à-dire choisir le bon outil, avec les bons paramètres, et reformuler correctement le résultat — ce qui est le cœur du endpoint `/mcp/chat`. C'est un critère de jugement qualitatif du développeur, corroboré par le fait qu'OpenAI a été un des premiers à standardiser et stabiliser ce format (`tools`/`tool_choice`), aujourd'hui repris par les autres providers.
2. **Contrainte pratique d'accès aux clés API** : au moment de réaliser ce test, seule une clé API OpenAI était disponible/accessible pour le développeur. Les autres providers mentionnés dans l'énoncé (Anthropic Claude, Google Gemini, Llama via un fournisseur d'inférence, Mistral) nécessitent chacun la création d'un compte et l'obtention d'une clé API séparée, ce qui n'était pas réalisable dans le délai imparti. Le choix d'OpenAI n'élimine donc pas les autres options sur le fond — il a permis de livrer une implémentation **fonctionnelle de bout en bout** dans le temps disponible.

Le modèle `gpt-4o-mini` (plutôt que GPT-4o ou GPT-4.1) a ensuite été retenu pour sa **fiabilité en function-calling à un coût très faible** (~0,15 $ / 0,60 $ par million de tokens), largement suffisant pour 5 outils déterministes et des conversations courtes. Le code est conçu pour que ce choix reste réversible : le modèle est configurable via `OPENAI_MODEL`, et `chat.py` n'utilise aucune fonctionnalité propriétaire au-delà du format `tools` standard — **migrer vers Claude Sonnet, Gemini 2.5 Flash ou un modèle Llama/Mistral auto-hébergé ne nécessiterait que de remplacer le client SDK et la fonction d'appel**, sans changer la logique métier (`execute_tool`, `TOOLS_DEFINITION`, schémas Pydantic).

## 4. Confidentialité, sécurité et conformité (RGPD / souveraineté des données)

Pour une plateforme eGov manipulant potentiellement des données fiscales et personnelles de citoyens/entreprises ivoiriens, le choix du provider LLM a des implications de conformité au-delà du coût et de la performance :

- **Données envoyées au LLM** : actuellement, seuls les messages de conversation et les résultats d'outils (calculs fiscaux génériques, taux de change) transitent vers OpenAI — aucune donnée d'identification personnelle (nom, NCC, numéro de compte) n'est collectée ni envoyée par l'application dans son état actuel.
- **Politique de rétention OpenAI** : par défaut, l'API OpenAI (hors ChatGPT grand public) ne réutilise pas les données envoyées via l'API pour entraîner ses modèles, et propose une rétention limitée (configurable via le mode "Zero Data Retention" pour les comptes éligibles). À vérifier/contractualiser si des données personnelles devaient transiter à l'avenir.
- **Localisation des données** : les API OpenAI, Anthropic et Google traitent les données sur des serveurs hors d'Afrique de l'Ouest (principalement US/UE). Pour une plateforme gouvernementale ivoirienne, cela peut poser une question de **souveraineté numérique** — un argument en faveur, à terme, de modèles **open-weight auto-hébergeables** (Llama, Mistral) sur une infrastructure locale ou régionale (ex. cloud africain ou européen avec garanties contractuelles).
- **RGPD / lois locales sur la protection des données** : si FIDELIA venait à traiter des données personnelles identifiables, il faudrait (1) un accord de traitement des données (DPA) avec le provider LLM, (2) une anonymisation/pseudonymisation des données avant envoi au LLM lorsque possible, et (3) idéalement un hébergement des modèles dans une juridiction conforme à la réglementation ivoirienne sur la protection des données à caractère personnel.
- **Recommandation pour une mise en production** : conserver `gpt-4o-mini` (ou équivalent) pour le prototypage et les fonctionnalités à faible sensibilité, mais évaluer une bascule vers un modèle **open-weight auto-hébergé** (Llama 4 / Mistral) pour les flux impliquant des données personnelles, afin de garder le contrôle total sur la localisation et la rétention des données — ce que l'architecture actuelle permet sans refonte majeure (cf. section précédente).

## 5. Orchestration : function-calling, pas de framework d'agents

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
