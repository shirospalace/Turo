"""Sunsky-Online Open API client (Phase 2 — needs Sunsky Open API access).

Sunsky's exact auth scheme depends on their developer docs (typically an
API key/secret pair signed per-request); confirm details once API access is
granted. Intended use here: pull product data (price, stock, warehouse) and
create orders programmatically, replacing the CSV import path.

This module is a stub: it validates credentials are present and returns a
clear "not configured" result otherwise. Until then, use the CSV import
(services/sunsky_csv.py) or manual product entry — both work today.
"""
from services.api_config import sunsky_credentials


def fetch_product(sku: str):
    creds = sunsky_credentials()
    if not creds["configured"]:
        return {
            "configured": False,
            "message": (
                "Sunsky API not connected. Set SUNSKY_API_KEY and SUNSKY_API_SECRET "
                "(from a Sunsky Open API access request) as environment variables, "
                "then restart the app. Use CSV import or manual entry in the meantime."
            ),
            "product": None,
        }

    raise NotImplementedError(
        "Sunsky credentials are set but the live Open API call isn't wired up yet."
    )


def create_order(sunsky_sku: str, shipping_address: dict, quantity: int = 1):
    creds = sunsky_credentials()
    if not creds["configured"]:
        return {
            "configured": False,
            "message": (
                "Sunsky API not connected. Place this order manually on Sunsky "
                "and log the resulting Sunsky order ID in the Orders tab."
            ),
        }

    raise NotImplementedError(
        "Sunsky credentials are set but order creation isn't wired up yet."
    )
