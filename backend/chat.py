import logging

from openai import AsyncOpenAI
from config import settings
from tools.convert_currency import convert_currency
from tools.calculate_vat import calculate_vat
from tools.tax_deadlines import get_tax_deadlines
from tools.calculate_cnps import calculate_cnps
from tools.search_tax_code import search_tax_code
import json

logger = logging.getLogger("fidelia.chat")

client = AsyncOpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """Tu es FIDELIA, un assistant fiscal et administratif intelligent pour la Côte d'Ivoire.
Tu aides les citoyens et entreprises avec : la FNE/DGI, la TVA, les échéances fiscales, le CNPS, et le Code Général des Impôts.
Réponds en français ou anglais selon la langue de l'utilisateur.
Sois précis, professionnel et bienveillant.
Quand tu utilises un outil, explique brièvement le résultat à l'utilisateur."""

TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "Convertit un montant entre devises (FCFA/XOF, EUR, USD, ...) à l'aide de taux de change publics, utile pour les factures FNE en devise étrangère (template B2F)",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Montant à convertir"},
                    "from_currency": {"type": "string", "description": "Devise source, ex: XOF (FCFA), EUR, USD"},
                    "to_currency": {"type": "string", "description": "Devise cible, ex: EUR, USD, XOF"}
                },
                "required": ["amount", "from_currency", "to_currency"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_vat",
            "description": "Calcule la TVA selon le Code Général des Impôts ivoirien (taux 18%, 9%, 0%)",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount_ht": {"type": "number", "description": "Montant hors taxe en FCFA"},
                    "tva_type": {"type": "string", "enum": ["TVA", "TVAB", "TVAC", "TVAD"], "description": "Type de TVA. TVA=18%, TVAB=9%, TVAC/TVAD=0%"}
                },
                "required": ["amount_ht"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_tax_deadlines",
            "description": "Retourne les échéances fiscales DGI Côte d'Ivoire 2025",
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_type": {"type": "string", "enum": ["TVA", "IS", "CNPS", "DSF", "Patente"], "description": "Filtrer par type d'échéance (optionnel)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_cnps",
            "description": "Calcule les cotisations CNPS selon le barème officiel ivoirien",
            "parameters": {
                "type": "object",
                "properties": {
                    "salaire_brut": {"type": "number", "description": "Salaire brut mensuel en FCFA"},
                    "nb_employes": {"type": "integer", "description": "Nombre d'employés (défaut: 1)"}
                },
                "required": ["salaire_brut"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_tax_code",
            "description": "Recherche dans le Code Général des Impôts de Côte d'Ivoire",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Terme à rechercher dans le CGI"}
                },
                "required": ["query"]
            }
        }
    }
]

async def execute_tool(tool_name: str, args: dict) -> dict:
    if tool_name == "convert_currency":
        return await convert_currency(args["amount"], args.get("from_currency", "XOF"), args.get("to_currency", "EUR"))
    elif tool_name == "calculate_vat":
        return calculate_vat(args["amount_ht"], args.get("tva_type", "TVA"))
    elif tool_name == "get_tax_deadlines":
        return get_tax_deadlines(args.get("filter_type"))
    elif tool_name == "calculate_cnps":
        return calculate_cnps(args["salaire_brut"], args.get("nb_employes", 1))
    elif tool_name == "search_tax_code":
        return search_tax_code(args["query"])
    return {"error": "Outil inconnu"}

async def chat_with_tools(messages: list) -> dict:
    # Appel initial à GPT avec les outils disponibles
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        tools=TOOLS_DEFINITION,
        tool_choice="auto",
    )

    message = response.choices[0].message
    tool_used = None
    tool_data = None

    # Si GPT veut utiliser un outil
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        # Exécuter le vrai outil MCP
        logger.info("Appel outil '%s' avec args=%s", tool_name, tool_args)
        tool_result = await execute_tool(tool_name, tool_args)
        tool_used = tool_name
        tool_data = tool_result

        # Deuxième appel avec le résultat de l'outil
        messages_with_result = (
            [{"role": "system", "content": SYSTEM_PROMPT}]
            + messages
            + [
                {"role": "assistant", "content": None, "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {"name": tool_name, "arguments": tool_call.function.arguments}
                    }
                ]},
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False)
                }
            ]
        )

        final_response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages_with_result,
        )
        final_text = final_response.choices[0].message.content
    else:
        final_text = message.content

    return {
        "text": final_text,
        "tool_used": tool_used,
        "tool_data": tool_data,
    }
