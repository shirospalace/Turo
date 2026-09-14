"""eBay Browse API client (Phase 2 — needs an eBay Developer Program app).

Auth: OAuth2 client-credentials flow against
  POST https://api.ebay.com/identity/v1/oauth2/token
using EBAY_APP_ID (Client ID) + EBAY_CERT_ID (Client Secret) with scope
"https://api.ebay.com/oauth/api_scope" to get an application access token
(no user login needed — this is the public Browse API).

Search comps:
  GET https://api.ebay.com/buy/browse/v1/item_summary/search?q={query}
  Header: Authorization: Bearer {token}

Default rate limit on the standard tier is ~5000 calls/day; cache/space out
calls accordingly once wired up.

This module is a stub: it validates credentials are present and returns a
clear "not configured" result otherwise, so the rest of the app never
breaks while waiting on your eBay Developer Program registration.
"""
from services.api_config import ebay_credentials


def search_comps(query: str, limit: int = 10):
    creds = ebay_credentials()
    if not creds["configured"]:
        return {
            "configured": False,
            "message": (
                "eBay API not connected. Set EBAY_APP_ID and EBAY_CERT_ID "
                "(from an eBay Developer Program app) as environment variables, "
                "then restart the app. Use manual comp entry in the meantime."
            ),
            "results": [],
        }

    # Real implementation (once credentials exist):
    #   1. POST to the OAuth token endpoint with client_credentials grant to get
    #      a bearer token (cache it — tokens are valid ~2 hours).
    #   2. GET the Browse API search endpoint with that token and `query`.
    #   3. Map item_summary results to {title, price, url}.
    raise NotImplementedError(
        "eBay credentials are set but the live Browse API call isn't wired up yet."
    )
