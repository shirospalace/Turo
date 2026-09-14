from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db, MarketplaceFeeConfig, Category
from schemas import FeeConfigIn, FeeConfigOut, CategoryIn, CategoryOut

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/fee-configs", response_model=list[FeeConfigOut])
def list_fee_configs(db: Session = Depends(get_db)):
    return db.query(MarketplaceFeeConfig).order_by(MarketplaceFeeConfig.marketplace).all()


@router.put("/fee-configs/{marketplace}", response_model=FeeConfigOut)
def update_fee_config(marketplace: str, payload: FeeConfigIn, db: Session = Depends(get_db)):
    cfg = db.query(MarketplaceFeeConfig).filter_by(marketplace=marketplace).first()
    if not cfg:
        raise HTTPException(404, f"No fee config for marketplace '{marketplace}'")
    for field, value in payload.model_dump().items():
        setattr(cfg, field, value)
    db.commit()
    db.refresh(cfg)
    return cfg


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()


@router.post("/categories", response_model=CategoryOut)
def create_category(payload: CategoryIn, db: Session = Depends(get_db)):
    if db.query(Category).filter_by(name=payload.name).first():
        raise HTTPException(400, "Category already exists")
    cat = Category(**payload.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat
