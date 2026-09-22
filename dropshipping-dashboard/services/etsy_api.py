"""Etsy Open API v3 client (Phase 2 — needs an Etsy Developer app).

Auth: public listing search only needs the API keystring (no OAuth):
  GET https://openapi.etsy.com/v3/application/listings/active?keywords={query}
  Header: x-api-key: {ETSY_API_KEY}

Rate limits on standard access: ~10 requests/second, 10,000 requests/day.

This module is a stub: it validates the API key is present and returns a
clear "not configured" result otherwise, so the rest of the app never
breaks while waiting on your Etsy Developer app registration.
"""
from services.api_config import etsy_credentials


def search_comps(query: str, limit: int = 10):
    creds = etsy_credentials()
    if not creds["configured"]:
        return {
            "configured": False,
            "message": (
                "Etsy API not connected. Set ETSY_API_KEY (from an Etsy Developer "
                "app's keystring) as an environment variable, then restart the app. "
                "Use manual comp entry in the meantime."
            ),
            "results": [],
        }

    # Real implementation (once credentials exist):
    #   GET the listings/active endpoint with x-api-key header and `keywords`.
    #   Map results to {title, price, url}.
    raise NotImplementedError(
        "Etsy credentials are set but the live Open API v3 call isn't wired up yet."
    )
