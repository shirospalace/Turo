from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db, ListingDraft, Product, ListingPrice
from schemas import ListingDraftIn, ListingDraftOut
from services.listing_generator import generate_draft

router = APIRouter(prefix="/api/products/{product_id}/drafts", tags=["listings"])


@router.get("", response_model=list[ListingDraftOut])
def list_drafts(product_id: int, db: Session = Depends(get_db)):
    if not db.get(Product, product_id):
        raise HTTPException(404, "Product not found")
    drafts = db.query(ListingDraft).filter_by(product_id=product_id).all()
    return [ListingDraftOut.model_validate({**d.__dict__, "tags": d.tags}) for d in drafts]


@router.post("/generate/{marketplace}", response_model=ListingDraftOut)
def generate(product_id: int, marketplace: str, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    if marketplace not in ("amazon", "ebay", "etsy"):
        raise HTTPException(400, "Unknown marketplace")

    lp = db.query(ListingPrice).filter_by(product_id=product_id, marketplace=marketplace).first()
    target_price = lp.target_sale_price if lp else round(product.cost * 3, 2)

    generated = generate_draft(product, marketplace, target_price)
    draft = ListingDraft(product_id=product_id, marketplace=marketplace, title=generated["title"], body=generated["body"], price=generated["price"])
    draft.tags = generated["tags"]
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return ListingDraftOut.model_validate({**draft.__dict__, "tags": draft.tags})


@router.put("/{draft_id}", response_model=ListingDraftOut)
def update_draft(product_id: int, draft_id: int, payload: ListingDraftIn, db: Session = Depends(get_db)):
    draft = db.get(ListingDraft, draft_id)
    if not draft or draft.product_id != product_id:
        raise HTTPException(404, "Draft not found")
    from db import now

    draft.title = payload.title
    draft.body = payload.body
    draft.tags = payload.tags
    draft.price = payload.price
    draft.edited_at = now()
    db.commit()
    db.refresh(draft)
    return ListingDraftOut.model_validate({**draft.__dict__, "tags": draft.tags})


@router.delete("/{draft_id}")
def delete_draft(product_id: int, draft_id: int, db: Session = Depends(get_db)):
    draft = db.get(ListingDraft, draft_id)
    if not draft or draft.product_id != product_id:
        raise HTTPException(404, "Draft not found")
    db.delete(draft)
    db.commit()
    return {"ok": True}
