from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db import get_db, Order, Product, ReturnRecord, now
from schemas import OrderIn, OrderOut, ReturnIn, ReturnOut, SummaryRow

router = APIRouter(prefix="/api", tags=["orders"])


def _order_out(order: Order) -> OrderOut:
    data = {
        "id": order.id,
        "marketplace": order.marketplace,
        "marketplace_order_id": order.marketplace_order_id,
        "product_id": order.product_id,
        "product_title": order.product.title if order.product else "",
        "sale_price": order.sale_price,
        "order_date": order.order_date,
        "sunsky_order_id": order.sunsky_order_id,
        "status": order.status,
        "tracking_number": order.tracking_number,
        "notes": order.notes,
        "return_status": order.return_record.status if order.return_record else "none",
    }
    return OrderOut.model_validate(data)


@router.get("/orders", response_model=list[OrderOut])
def list_orders(
    status: Optional[str] = None,
    marketplace: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if marketplace:
        q = q.filter(Order.marketplace == marketplace)
    orders = q.order_by(Order.order_date.desc()).all()
    return [_order_out(o) for o in orders]


@router.post("/orders", response_model=OrderOut)
def create_order(payload: OrderIn, db: Session = Depends(get_db)):
    if not db.get(Product, payload.product_id):
        raise HTTPException(400, "Unknown product_id")
    data = payload.model_dump()
    if not data.get("order_date"):
        data["order_date"] = now()
    order = Order(**data)
    db.add(order)
    db.commit()
    db.refresh(order)
    return _order_out(order)


@router.put("/orders/{order_id}", response_model=OrderOut)
def update_order(order_id: int, payload: OrderIn, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    data = payload.model_dump()
    if not data.get("order_date"):
        data["order_date"] = order.order_date
    for field, value in data.items():
        setattr(order, field, value)
    db.commit()
    db.refresh(order)
    return _order_out(order)


@router.delete("/orders/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    db.delete(order)
    db.commit()
    return {"ok": True}


@router.get("/orders/{order_id}/return", response_model=Optional[ReturnOut])
def get_return(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order.return_record


@router.put("/orders/{order_id}/return", response_model=ReturnOut)
def upsert_return(order_id: int, payload: ReturnIn, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    record = order.return_record
    if record:
        for field, value in payload.model_dump().items():
            setattr(record, field, value)
        record.updated_at = now()
    else:
        record = ReturnRecord(order_id=order_id, **payload.model_dump())
        db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/summary", response_model=list[SummaryRow])
def summary(
    group_by: str = Query("month", pattern="^(week|month)$"),
    marketplace: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Order)
    if marketplace:
        q = q.filter(Order.marketplace == marketplace)
    orders = q.all()

    def period_key(dt):
        if group_by == "week":
            iso = dt.isocalendar()
            return f"{iso[0]}-W{iso[1]:02d}"
        return dt.strftime("%Y-%m")

    buckets = defaultdict(lambda: {"revenue": 0.0, "cost": 0.0, "refunds": 0.0, "order_count": 0})
    for order in orders:
        key = (period_key(order.order_date), order.marketplace)
        b = buckets[key]
        b["revenue"] += order.sale_price
        b["cost"] += order.product.cost if order.product else 0.0
        if order.return_record and order.return_record.status == "refunded":
            b["refunds"] += order.return_record.refund_amount
        b["order_count"] += 1

    rows = []
    for (period, mp), b in sorted(buckets.items()):
        net_profit = b["revenue"] - b["cost"] - b["refunds"]
        rows.append(
            SummaryRow(
                period=period,
                marketplace=mp,
                revenue=round(b["revenue"], 2),
                cost=round(b["cost"], 2),
                refunds=round(b["refunds"], 2),
                net_profit=round(net_profit, 2),
                order_count=b["order_count"],
            )
        )
    return rows
