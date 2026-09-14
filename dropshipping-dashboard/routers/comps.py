from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db, CompPrice, Product
from schemas import CompPriceIn, CompPriceOut

router = APIRouter(prefix="/api/products/{product_id}/comps", tags=["comps"])


def _get_product_or_404(product_id: int, db: Session) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product


@router.get("", response_model=list[CompPriceOut])
def list_comps(product_id: int, marketplace: str | None = None, db: Session = Depends(get_db)):
    _get_product_or_404(product_id, db)
    q = db.query(CompPrice).filter_by(product_id=product_id)
    if marketplace:
        q = q.filter_by(marketplace=marketplace)
    return q.order_by(CompPrice.captured_at.desc()).all()


@router.get("/latest", response_model=list[CompPriceOut])
def latest_comps(product_id: int, db: Session = Depends(get_db)):
    """Most recent comp per marketplace, for the research-tab summary row."""
    _get_product_or_404(product_id, db)
    all_comps = (
        db.query(CompPrice)
        .filter_by(product_id=product_id)
        .order_by(CompPrice.captured_at.desc())
        .all()
    )
    seen = set()
    latest = []
    for c in all_comps:
        if c.marketplace not in seen:
            seen.add(c.marketplace)
            latest.append(c)
    return latest


@router.post("", response_model=CompPriceOut)
def add_comp(product_id: int, payload: CompPriceIn, db: Session = Depends(get_db)):
    _get_product_or_404(product_id, db)
    comp = CompPrice(product_id=product_id, **payload.model_dump())
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return comp


@router.delete("/{comp_id}")
def delete_comp(product_id: int, comp_id: int, db: Session = Depends(get_db)):
    comp = db.get(CompPrice, comp_id)
    if not comp or comp.product_id != product_id:
        raise HTTPException(404, "Comp not found")
    db.delete(comp)
    db.commit()
    return {"ok": True}
