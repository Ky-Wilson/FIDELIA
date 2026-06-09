import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

import main
import mcp_server


@pytest.fixture
def client():
    return TestClient(main.app)


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "convert_currency" in data["tools"]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_tools(client):
    response = client.get("/mcp/tools")
    assert response.status_code == 200
    names = [t["name"] for t in response.json()["tools"]]
    assert names == [
        "convert_currency",
        "calculate_vat",
        "get_tax_deadlines",
        "calculate_cnps",
        "search_tax_code",
    ]


def test_calculate_vat_endpoint(client):
    response = client.post("/mcp/tools/calculate_vat", json={"amount_ht": 100000, "tva_type": "TVA"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["tva_amount"] == 18000


def test_calculate_cnps_endpoint(client):
    response = client.post("/mcp/tools/calculate_cnps", json={"salaire_brut": 300000, "nb_employes": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["nb_employes"] == 2


def test_get_tax_deadlines_endpoint(client):
    response = client.post("/mcp/tools/get_tax_deadlines", json={"filter_type": "CNPS"})
    assert response.status_code == 200
    data = response.json()
    assert all(e["type"] == "CNPS" for e in data["echeances"])


def test_search_tax_code_endpoint(client):
    response = client.post("/mcp/tools/search_tax_code", json={"query": "patente"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] >= 1


def test_convert_currency_endpoint(client, monkeypatch):
    async def fake_convert_currency(amount, from_currency, to_currency):
        return {
            "success": True,
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": 0.0015,
            "converted_amount": amount * 0.0015,
            "date": "Mon, 09 Jun 2026 00:00:00 +0000",
            "source": "test",
        }

    monkeypatch.setattr(mcp_server, "convert_currency", fake_convert_currency)

    response = client.post("/mcp/tools/convert_currency", json={"amount": 1000, "from_currency": "XOF", "to_currency": "EUR"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["converted_amount"] == 1.5


def test_chat_endpoint(client, monkeypatch):
    fake_result = {"text": "Bonjour !", "tool_used": None, "tool_data": None}
    monkeypatch.setattr(mcp_server, "chat_with_tools", AsyncMock(return_value=fake_result))

    response = client.post("/mcp/chat", json={"messages": [{"role": "user", "content": "Bonjour"}]})
    assert response.status_code == 200
    assert response.json() == fake_result


def test_chat_endpoint_error_returns_502(client, monkeypatch):
    monkeypatch.setattr(mcp_server, "chat_with_tools", AsyncMock(side_effect=RuntimeError("boom")))

    response = client.post("/mcp/chat", json={"messages": [{"role": "user", "content": "Bonjour"}]})
    assert response.status_code == 502


def test_api_key_required_when_configured(client, monkeypatch):
    from auth import settings as auth_settings
    monkeypatch.setattr(auth_settings, "mcp_api_key", "secret123")

    response = client.post("/mcp/tools/calculate_vat", json={"amount_ht": 1000})
    assert response.status_code == 401

    response = client.post(
        "/mcp/tools/calculate_vat",
        json={"amount_ht": 1000},
        headers={"X-API-Key": "secret123"},
    )
    assert response.status_code == 200
