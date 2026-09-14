"""SQLAlchemy engine, session, and ORM models for the dropshipping dashboard."""
import datetime
import json
import os

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dropshipping.db")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def now():
    return datetime.datetime.utcnow()


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    # Not used for purses; flagged for future categories (food/cosmetics/supplements)
    # that would need a halal-compliance review before sourcing.
    halal_review_needed = Column(Boolean, default=False)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    sunsky_sku = Column(String, default="")
    source_url = Column(String, default="")
    cost = Column(Float, nullable=False, default=0.0)
    weight_g = Column(Float, default=0.0)
    warehouse_location = Column(String, default="CN")  # CN/HK/US/EU-UK/UAE
    est_ship_days = Column(Integer, default=0)
    images_json = Column(Text, default="[]")  # JSON list of image URLs
    status = Column(String, default="researching")  # researching/approved/rejected
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=now)

    category = relationship("Category", back_populates="products")
    listing_prices = relationship(
        "ListingPrice", back_populates="product", cascade="all, delete-orphan"
    )
    comps = relationship("CompPrice", back_populates="product", cascade="all, delete-orphan")
    drafts = relationship("ListingDraft", back_populates="product", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="product")

    @property
    def images(self):
        try:
            return json.loads(self.images_json or "[]")
        except (TypeError, ValueError):
            return []

    @images.setter
    def images(self, value):
        self.images_json = json.dumps(value or [])


class MarketplaceFeeConfig(Base):
    """Generic fee model covering Amazon/eBay/Etsy with one formula:
    fees = listing_fee + sale_price*(variable_pct_1+variable_pct_2)/100
           + fixed_fee_1 + fixed_fee_2
    See services/margin.py for how each field maps per marketplace.
    """

    __tablename__ = "marketplace_fee_configs"

    id = Column(Integer, primary_key=True)
    marketplace = Column(String, unique=True, nullable=False)  # amazon/ebay/etsy
    listing_fee = Column(Float, default=0.0)
    variable_pct_1 = Column(Float, default=0.0)
    fixed_fee_1 = Column(Float, default=0.0)
    variable_pct_2 = Column(Float, default=0.0)
    fixed_fee_2 = Column(Float, default=0.0)
    notes = Column(Text, default="")


class ListingPrice(Base):
    __tablename__ = "listing_prices"
    __table_args__ = (UniqueConstraint("product_id", "marketplace", name="uq_product_marketplace"),)

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    marketplace = Column(String, nullable=False)
    target_sale_price = Column(Float, default=0.0)
    shipping_cost_estimate = Column(Float, default=0.0)

    product = relationship("Product", back_populates="listing_prices")


class CompPrice(Base):
    __tablename__ = "comp_prices"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    marketplace = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    title = Column(String, default="")
    url = Column(String, default="")
    source = Column(String, default="manual")  # manual/api
    captured_at = Column(DateTime, default=now)

    product = relationship("Product", back_populates="comps")


class ListingDraft(Base):
    __tablename__ = "listing_drafts"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    marketplace = Column(String, nullable=False)
    title = Column(Text, default="")
    body = Column(Text, default="")
    tags_json = Column(Text, default="[]")
    price = Column(Float, default=0.0)
    generated_at = Column(DateTime, default=now)
    edited_at = Column(DateTime, default=now)

    product = relationship("Product", back_populates="drafts")

    @property
    def tags(self):
        try:
            return json.loads(self.tags_json or "[]")
        except (TypeError, ValueError):
            return []

    @tags.setter
    def tags(self, value):
        self.tags_json = json.dumps(value or [])


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    marketplace = Column(String, nullable=False)
    marketplace_order_id = Column(String, default="")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sale_price = Column(Float, nullable=False, default=0.0)
    order_date = Column(DateTime, default=now)
    sunsky_order_id = Column(String, default="")
    status = Column(String, default="needs_sourcing")
    # needs_sourcing/ordered_on_sunsky/shipped/delivered
    tracking_number = Column(String, default="")
    notes = Column(Text, default="")

    product = relationship("Product", back_populates="orders")
    return_record = relationship(
        "ReturnRecord", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )


class ReturnRecord(Base):
    __tablename__ = "return_records"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)
    status = Column(String, default="none")  # none/requested/approved/refunded/denied
    reason = Column(Text, default="")
    refund_amount = Column(Float, default=0.0)
    notes = Column(Text, default="")
    updated_at = Column(DateTime, default=now)

    order = relationship("Order", back_populates="return_record")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
