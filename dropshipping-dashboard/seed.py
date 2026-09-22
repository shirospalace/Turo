"""Seed default category and marketplace fee configs on first run (idempotent)."""
from db import SessionLocal, Category, MarketplaceFeeConfig

DEFAULT_FEE_CONFIGS = [
    dict(
        marketplace="amazon",
        listing_fee=0.0,
        variable_pct_1=15.0,  # referral fee, purses/handbags category
        fixed_fee_1=0.0,
        variable_pct_2=0.0,
        fixed_fee_2=0.0,
        notes="Referral fee ~15% for handbags/accessories. Shipping cost entered per-listing (FBM estimate).",
    ),
    dict(
        marketplace="ebay",
        listing_fee=0.0,
        variable_pct_1=13.25,  # final value fee
        fixed_fee_1=0.30,
        variable_pct_2=0.0,
        fixed_fee_2=0.0,
        notes="Final value fee ~13.25% + $0.30 per order.",
    ),
    dict(
        marketplace="etsy",
        listing_fee=0.20,
        variable_pct_1=6.5,  # transaction fee
        fixed_fee_1=0.0,
        variable_pct_2=3.0,  # payment processing
        fixed_fee_2=0.25,
        notes="Listing fee $0.20 + transaction fee 6.5% + payment processing ~3% + $0.25.",
    ),
]


def seed(db=None):
    owns_session = db is None
    db = db or SessionLocal()
    try:
        if not db.query(Category).filter_by(name="Purses").first():
            db.add(Category(name="Purses", halal_review_needed=False))

        existing = {c.marketplace for c in db.query(MarketplaceFeeConfig).all()}
        for cfg in DEFAULT_FEE_CONFIGS:
            if cfg["marketplace"] not in existing:
                db.add(MarketplaceFeeConfig(**cfg))

        db.commit()
    finally:
        if owns_session:
            db.close()


if __name__ == "__main__":
    from db import init_db

    init_db()
    seed()
    print("Seeded database.")
