
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db
from models import Order, OrderStatus
from schemas import OrderCreate, OrderResponse, OrderUpdate
from utils import calculate_total, get_customer_or_404, get_order_or_404

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    get_customer_or_404(db, payload.customer_id)  # order must belong to an existing customer
    order = Order(
        customer_id=payload.customer_id,
        product_name=payload.product_name,
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        total_amount=calculate_total(payload.quantity, payload.unit_price),
        order_status=payload.order_status,
    )
    try:
        db.add(order)
        db.commit()
        db.refresh(order)
    except SQLAlchemyError:
        db.rollback()
        raise
    return order


@router.get("", response_model=List[OrderResponse])
def list_orders(
    customer_id: Optional[int] = Query(None, gt=0, description="Filter by customer"),
    order_status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(Order).order_by(Order.order_id)
    if customer_id is not None:
        stmt = stmt.where(Order.customer_id == customer_id)
    if order_status is not None:
        stmt = stmt.where(Order.order_status == order_status)
    return db.scalars(stmt.offset(skip).limit(limit)).all()


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    return get_order_or_404(db, order_id)


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, payload: OrderUpdate, db: Session = Depends(get_db)):
    order = get_order_or_404(db, order_id)
    get_customer_or_404(db, payload.customer_id)  # new owner must also exist
    order.customer_id = payload.customer_id
    order.product_name = payload.product_name
    order.quantity = payload.quantity
    order.unit_price = payload.unit_price
    order.order_status = payload.order_status
    order.total_amount = calculate_total(payload.quantity, payload.unit_price)
    try:
        db.commit()
        db.refresh(order)
    except SQLAlchemyError:
        db.rollback()
        raise
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = get_order_or_404(db, order_id)
    try:
        db.delete(order)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return None
