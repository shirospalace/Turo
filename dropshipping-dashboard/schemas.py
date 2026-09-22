"""Pydantic request/response models shared across routers."""
import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

MARKETPLACES = ["amazon", "ebay", "etsy"]
WAREHOUSES = ["CN", "HK", "US", "EU-UK", "UAE"]
PRODUCT_STATUSES = ["researching", "approved", "rejected"]
ORDER_STATUSES = ["needs_sourcing", "ordered_on_sunsky", "shipped", "delivered"]
RETURN_STATUSES = ["none", "requested", "approved", "refunded", "denied"]


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    halal_review_needed: bool


class CategoryIn(BaseModel):
    name: str
    halal_review_needed: bool = False


class FeeConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    marketplace: str
    listing_fee: float
    variable_pct_1: float
    fixed_fee_1: float
    variable_pct_2: float
    fixed_fee_2: float
    notes: str


class FeeConfigIn(BaseModel):
    listing_fee: float = 0.0
    variable_pct_1: float = 0.0
    fixed_fee_1: float = 0.0
    variable_pct_2: float = 0.0
    fixed_fee_2: float = 0.0
    notes: str = ""


class ListingPriceIn(BaseModel):
    marketplace: str
    target_sale_price: float = 0.0
    shipping_cost_estimate: float = 0.0


class ListingPriceOut(ListingPriceIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class MarginOut(BaseModel):
    marketplace: str
    sale_price: float
    cost: float
    shipping_cost_estimate: float
    fees: float
    net_profit: float
    margin_pct: float
    markup_pct: float
    below_threshold: bool


class ProductIn(BaseModel):
    category_id: int
    title: str
    description: str = ""
    sunsky_sku: str = ""
    source_url: str = ""
    cost: float = 0.0
    weight_g: float = 0.0
    warehouse_location: str = "CN"
    est_ship_days: int = 0
    images: List[str] = []
    status: str = "researching"
    notes: str = ""


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category_id: int
    title: str
    description: str
    sunsky_sku: str
    source_url: str
    cost: float
    weight_g: float
    warehouse_location: str
    est_ship_days: int
    images: List[str]
    status: str
    notes: str
    created_at: datetime.datetime


class ProductWithMargins(ProductOut):
    category_name: str = ""
    listing_prices: List[ListingPriceOut] = []
    margins: List[MarginOut] = []


class CompPriceIn(BaseModel):
    marketplace: str
    price: float
    title: str = ""
    url: str = ""
    source: str = "manual"


class CompPriceOut(CompPriceIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    captured_at: datetime.datetime


class ListingDraftIn(BaseModel):
    marketplace: str
    title: str = ""
    body: str = ""
    tags: List[str] = []
    price: float = 0.0


class ListingDraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    marketplace: str
    title: str
    body: str
    tags: List[str]
    price: float
    generated_at: datetime.datetime
    edited_at: datetime.datetime


class OrderIn(BaseModel):
    marketplace: str
    marketplace_order_id: str = ""
    product_id: int
    sale_price: float = 0.0
    order_date: Optional[datetime.datetime] = None
    sunsky_order_id: str = ""
    status: str = "needs_sourcing"
    tracking_number: str = ""
    notes: str = ""


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    marketplace: str
    marketplace_order_id: str
    product_id: int
    product_title: str = ""
    sale_price: float
    order_date: datetime.datetime
    sunsky_order_id: str
    status: str
    tracking_number: str
    notes: str
    return_status: str = "none"


class ReturnIn(BaseModel):
    status: str = "requested"
    reason: str = ""
    refund_amount: float = 0.0
    notes: str = ""


class ReturnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int
    status: str
    reason: str
    refund_amount: float
    notes: str
    updated_at: datetime.datetime


class SummaryRow(BaseModel):
    period: str
    marketplace: str
    revenue: float
    cost: float
    refunds: float
    net_profit: float
    order_count: int
