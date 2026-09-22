from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional

from db import get_db, Product, Category, ListingPrice, MarketplaceFeeConfig
from schemas import (
    ProductIn,
    ProductOut,
    ProductWithMargins,
    ListingPriceIn,
    ListingPriceOut,
    MarginOut,
)
from services.margin import calculate_margin
from services.sunsky_csv import parse_sunsky_csv

router = APIRouter(prefix="/api/products", tags=["products"])

DEFAULT_MARGIN_THRESHOLD_PCT = 20.0


def _product_with_margins(product: Product, db: Session, margin_threshold: float) -> dict:
    fee_configs = {c.marketplace: c for c in db.query(MarketplaceFeeConfig).all()}
    margins = []
    for lp in product.listing_prices:
        cfg = fee_configs.get(lp.marketplace)
        if not cfg:
            continue
        result = calculate_margin(product.cost, lp.target_sale_price, lp.shipping_cost_estimate, cfg)
        margins.append(
            MarginOut(
                **result.__dict__,
                below_threshold=result.margin_pct < margin_threshold,
            )
        )

    data = ProductOut.model_validate(product).model_dump()
    data["category_name"] = product.category.name if product.category else ""
    data["listing_prices"] = [ListingPriceOut.model_validate(lp) for lp in product.listing_prices]
    data["margins"] = margins
    return data


@router.get("", response_model=list[ProductWithMargins])
def list_products(
    category_id: Optional[int] = None,
    status: Optional[str] = None,
    margin_threshold: float = Query(DEFAULT_MARGIN_THRESHOLD_PCT),
    db: Session = Depends(get_db),
):
    q = db.query(Product)
    if category_id is not None:
        q = q.filter(Product.category_id == category_id)
    if status is not None:
        q = q.filter(Product.status == status)
    products = q.order_by(Product.created_at.desc()).all()
    return [_product_with_margins(p, db, margin_threshold) for p in products]


@router.get("/{product_id}", response_model=ProductWithMargins)
def get_product(product_id: int, margin_threshold: float = Query(DEFAULT_MARGIN_THRESHOLD_PCT), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return _product_with_margins(product, db, margin_threshold)


@router.post("", response_model=ProductWithMargins)
def create_product(payload: ProductIn, db: Session = Depends(get_db)):
    if not db.get(Category, payload.category_id):
        raise HTTPException(400, "Unknown category_id")
    data = payload.model_dump()
    images = data.pop("images")
    product = Product(**data)
    product.images = images
    db.add(product)
    db.commit()
    db.refresh(product)

    # Seed a listing_price row per known marketplace so the margin table has
    # something to show immediately; default target price = cost * 3 as a
    # rough starting point, fully editable afterwards.
    for cfg in db.query(MarketplaceFeeConfig).all():
        db.add(
            ListingPrice(
                product_id=product.id,
                marketplace=cfg.marketplace,
                target_sale_price=round(product.cost * 3, 2),
                shipping_cost_estimate=0.0,
            )
        )
    db.commit()
    db.refresh(product)
    return _product_with_margins(product, db, DEFAULT_MARGIN_THRESHOLD_PCT)


@router.put("/{product_id}", response_model=ProductWithMargins)
def update_product(product_id: int, payload: ProductIn, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    data = payload.model_dump()
    images = data.pop("images")
    for field, value in data.items():
        setattr(product, field, value)
    product.images = images
    db.commit()
    db.refresh(product)
    return _product_with_margins(product, db, DEFAULT_MARGIN_THRESHOLD_PCT)


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    db.delete(product)
    db.commit()
    return {"ok": True}


@router.put("/{product_id}/listing-price", response_model=ListingPriceOut)
def upsert_listing_price(product_id: int, payload: ListingPriceIn, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    lp = (
        db.query(ListingPrice)
        .filter_by(product_id=product_id, marketplace=payload.marketplace)
        .first()
    )
    if lp:
        lp.target_sale_price = payload.target_sale_price
        lp.shipping_cost_estimate = payload.shipping_cost_estimate
    else:
        lp = ListingPrice(product_id=product_id, **payload.model_dump())
        db.add(lp)
    db.commit()
    db.refresh(lp)
    return lp


@router.post("/import-csv")
def import_csv(category_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not db.get(Category, category_id):
        raise HTTPException(400, "Unknown category_id")
    content = file.file.read()
    rows, warnings = parse_sunsky_csv(content)

    fee_configs = db.query(MarketplaceFeeConfig).all()
    created = 0
    for row in rows:
        images = row.pop("images")
        product = Product(category_id=category_id, **row)
        product.images = images
        db.add(product)
        db.flush()  # get product.id
        for cfg in fee_configs:
            db.add(
                ListingPrice(
                    product_id=product.id,
                    marketplace=cfg.marketplace,
                    target_sale_price=round(product.cost * 3, 2),
                    shipping_cost_estimate=0.0,
                )
            )
        created += 1
    db.commit()
    return {"created": created, "warnings": warnings}
