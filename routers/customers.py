
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db
from models import Customer, Order
from schemas import CustomerCreate, CustomerResponse, CustomerUpdate
from utils import ensure_email_available, get_customer_or_404

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    ensure_email_available(db, payload.email)
    customer = Customer(**payload.model_dump())
    try:
        db.add(customer)
        db.commit()
        db.refresh(customer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "A customer with this email already exists")
    except SQLAlchemyError:
        db.rollback()
        raise
    return customer


@router.get("", response_model=List[CustomerResponse])
def list_customers(
    city: Optional[str] = Query(None, description="Filter by city"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(Customer).order_by(Customer.customer_id)
    if city:
        stmt = stmt.where(Customer.city.ilike(city.strip()))
    return db.scalars(stmt.offset(skip).limit(limit)).all()


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    return get_customer_or_404(db, customer_id)


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)):
    customer = get_customer_or_404(db, customer_id)
    ensure_email_available(db, payload.email, exclude_id=customer_id)
    for field, value in payload.model_dump().items():
        setattr(customer, field, value)
    try:
        db.commit()
        db.refresh(customer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "A customer with this email already exists")
    except SQLAlchemyError:
        db.rollback()
        raise
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = get_customer_or_404(db, customer_id)
    has_orders = db.scalars(
        select(Order.order_id).where(Order.customer_id == customer_id).limit(1)
    ).first()
    if has_orders is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a customer who has orders. Delete the orders first.",
        )
    try:
        db.delete(customer)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return None
