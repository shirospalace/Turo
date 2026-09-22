from fastapi import APIRouter

from services.api_config import integration_status
from services import ebay_api, etsy_api

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("/status")
def get_status():
    return integration_status()


@router.get("/ebay/search")
def ebay_search(q: str):
    return ebay_api.search_comps(q)


@router.get("/etsy/search")
def etsy_search(q: str):
    return etsy_api.search_comps(q)
