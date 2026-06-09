import httpx

SUPPORTED_CURRENCIES = ["XOF", "EUR", "USD", "GBP", "NGN", "GHS", "CNY", "MAD"]

async def convert_currency(amount: float, from_currency: str = "XOF", to_currency: str = "EUR") -> dict:
    """
    Convertit un montant entre devises (utile pour les factures FNE en
    devise étrangère, template B2F, qui exigent foreignCurrency/foreignCurrencyRate).
    Source : open.er-api.com (taux de change publics, mis à jour quotidiennement).
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if from_currency == to_currency:
        return {"success": False, "error": "La devise source et la devise cible sont identiques"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"https://open.er-api.com/v6/latest/{from_currency}")

            if response.status_code != 200:
                return {"success": False, "error": f"Erreur API taux de change: {response.status_code}"}

            data = response.json()
            if data.get("result") != "success":
                return {"success": False, "error": f"Devise source invalide: {from_currency}"}

            rates = data.get("rates", {})
            if to_currency not in rates:
                return {"success": False, "error": f"Devise cible inconnue: {to_currency}"}

            rate = rates[to_currency]
            converted_amount = round(amount * rate, 2)

            return {
                "success": True,
                "amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": rate,
                "converted_amount": converted_amount,
                "date": data.get("time_last_update_utc"),
                "source": "exchangerate-api.com (open.er-api.com)"
            }
    except httpx.TimeoutException:
        return {"success": False, "error": "Timeout — service de taux de change non accessible"}
    except Exception as e:
        return {"success": False, "error": str(e)}
