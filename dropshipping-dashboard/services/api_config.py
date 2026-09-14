"""Reads Phase-2 API credentials from environment variables.

None of these are required for the app to run — every feature that needs
them degrades to "not connected" in the UI instead of failing. Set the
relevant env vars once you have the accounts/API access from the
prerequisites checklist in the README.
"""
import os


def ebay_credentials():
    app_id = os.environ.get("EBAY_APP_ID", "")
    cert_id = os.environ.get("EBAY_CERT_ID", "")
    return {"app_id": app_id, "cert_id": cert_id, "configured": bool(app_id and cert_id)}


def etsy_credentials():
    api_key = os.environ.get("ETSY_API_KEY", "")
    return {"api_key": api_key, "configured": bool(api_key)}


def sunsky_credentials():
    api_key = os.environ.get("SUNSKY_API_KEY", "")
    api_secret = os.environ.get("SUNSKY_API_SECRET", "")
    return {"api_key": api_key, "api_secret": api_secret, "configured": bool(api_key and api_secret)}


def integration_status():
    return {
        "ebay": {
            "configured": ebay_credentials()["configured"],
            "requires": "eBay Developer Program app (App ID + Cert ID) as EBAY_APP_ID / EBAY_CERT_ID",
        },
        "etsy": {
            "configured": etsy_credentials()["configured"],
            "requires": "Etsy Developer app API keystring as ETSY_API_KEY",
        },
        "sunsky": {
            "configured": sunsky_credentials()["configured"],
            "requires": "Sunsky Open API key + secret as SUNSKY_API_KEY / SUNSKY_API_SECRET",
        },
    }
