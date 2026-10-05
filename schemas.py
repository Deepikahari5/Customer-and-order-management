
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from models import OrderStatus


def _clean_required(value: str, field: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field} must not be blank")
    return value


# ----------------------------- Customer -----------------------------------
class CustomerBase(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone_number: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)

    @field_validator("customer_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _clean_required(v, "Customer name")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        allowed = set("0123456789+-() ")
        digits = [c for c in v if c.isdigit()]
        if not set(v) <= allowed or not (7 <= len(digits) <= 15):
            raise ValueError(
                "Phone number must contain 7-15 digits (digits, +, -, spaces, brackets allowed)"
            )
        return v


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(CustomerBase):
    pass


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    customer_name: str
    email: str
    phone_number: Optional[str]
    address: Optional[str]
    city: Optional[str]
    created_date: datetime


# ------------------------------- Order ------------------------------------
class OrderBase(BaseModel):
    customer_id: int = Field(..., gt=0)
    product_name: str = Field(..., min_length=1, max_length=150)
    quantity: int = Field(..., gt=0, description="Must be greater than 0")
    unit_price: float = Field(..., gt=0, description="Must be greater than 0")
    order_status: OrderStatus = OrderStatus.PENDING

    @field_validator("product_name")
    @classmethod
    def validate_product(cls, v: str) -> str:
        return _clean_required(v, "Product name")


class OrderCreate(OrderBase):
    pass


class OrderUpdate(OrderBase):
    pass


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    customer_id: int
    product_name: str
    quantity: int
    unit_price: float
    total_amount: float
    order_status: OrderStatus
    order_date: datetime
