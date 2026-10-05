
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Customer, Order


def get_customer_or_404(db: Session, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} does not exist",
        )
    return customer


def get_order_or_404(db: Session, order_id: int) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} does not exist",
        )
    return order


def ensure_email_available(db: Session, email: str, exclude_id: Optional[int] = None) -> None:
    stmt = select(Customer).where(Customer.email == email)
    if exclude_id is not None:
        stmt = stmt.where(Customer.customer_id != exclude_id)
    if db.scalars(stmt).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A customer with email '{email}' already exists",
        )


def calculate_total(quantity: int, unit_price: float) -> float:
    return round(quantity * unit_price, 2)
