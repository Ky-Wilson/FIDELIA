import httpx
import pytest
import respx

from tools.calculate_vat import calculate_vat
from tools.calculate_cnps import calculate_cnps
from tools.tax_deadlines import get_tax_deadlines
from tools.search_tax_code import search_tax_code
from tools.convert_currency import convert_currency


# --- calculate_vat ---

def test_calculate_vat_taux_normal():
    result = calculate_vat(100000, "TVA")
    assert result["success"] is True
    assert result["tva_rate"] == "18%"
    assert result["tva_amount"] == 18000
    assert result["amount_ttc"] == 118000


def test_calculate_vat_taux_reduit():
    result = calculate_vat(100000, "TVAB")
    assert result["tva_rate"] == "9%"
    assert result["tva_amount"] == 9000


def test_calculate_vat_type_inconnu():
    result = calculate_vat(100000, "INVALID")
    assert result["success"] is False
    assert "INVALID" in result["error"]


# --- calculate_cnps ---

def test_calculate_cnps_un_employe():
    result = calculate_cnps(300000, 1)
    assert result["success"] is True
    assert result["base_cotisation"] == 300000
    assert result["part_employeur"]["total"] == round((0.0792 + 0.02 + 0.055) * 300000)
    assert result["part_salarie"]["total"] == round(0.036 * 300000)
    assert result["nb_employes"] == 1


def test_calculate_cnps_plafond():
    result = calculate_cnps(5_000_000, 1)
    assert result["base_cotisation"] == 1_647_315


def test_calculate_cnps_plusieurs_employes():
    result = calculate_cnps(300000, 5)
    assert result["total_global"] == result["total_par_employe"] * 5


# --- get_tax_deadlines ---

def test_get_tax_deadlines_all():
    result = get_tax_deadlines()
    assert result["success"] is True
    assert result["total"] == 9
    assert all("statut" in e for e in result["echeances"])


def test_get_tax_deadlines_filtered():
    result = get_tax_deadlines("TVA")
    assert result["success"] is True
    assert all(e["type"] == "TVA" for e in result["echeances"])
    assert result["total"] == 3


# --- search_tax_code ---

def test_search_tax_code_match():
    result = search_tax_code("TVA")
    assert result["success"] is True
    assert result["total"] > 0
    assert all("pertinence" in r for r in result["results"])


def test_search_tax_code_no_match():
    result = search_tax_code("inexistant_xyz")
    assert result["success"] is True
    assert result["total"] == 0
    assert result["results"] == []


# --- convert_currency ---

@pytest.mark.asyncio
async def test_convert_currency_success():
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://open.er-api.com/v6/latest/XOF").mock(
            return_value=httpx.Response(200, json={
                "result": "success",
                "time_last_update_utc": "Mon, 09 Jun 2026 00:00:00 +0000",
                "rates": {"EUR": 0.0015, "USD": 0.0016},
            })
        )
        result = await convert_currency(500000, "XOF", "EUR")

    assert result["success"] is True
    assert result["converted_amount"] == 750.0
    assert result["from_currency"] == "XOF"
    assert result["to_currency"] == "EUR"


@pytest.mark.asyncio
async def test_convert_currency_same_currency():
    result = await convert_currency(1000, "XOF", "XOF")
    assert result["success"] is False
    assert "identiques" in result["error"]


@pytest.mark.asyncio
async def test_convert_currency_unknown_target():
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://open.er-api.com/v6/latest/XOF").mock(
            return_value=httpx.Response(200, json={
                "result": "success",
                "time_last_update_utc": "Mon, 09 Jun 2026 00:00:00 +0000",
                "rates": {"EUR": 0.0015},
            })
        )
        result = await convert_currency(1000, "XOF", "ZZZ")

    assert result["success"] is False
    assert "inconnue" in result["error"]


@pytest.mark.asyncio
async def test_convert_currency_api_error():
    with respx.mock(assert_all_called=True) as mock:
        mock.get("https://open.er-api.com/v6/latest/XOF").mock(
            return_value=httpx.Response(500)
        )
        result = await convert_currency(1000, "XOF", "EUR")

    assert result["success"] is False
    assert "500" in result["error"]
