from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int


class PaymentCreate(BaseModel):
    amount: Decimal
    payment_method: str | None = None


class SaleCreate(BaseModel):
    business_id: int
    customer_id: int | None = None
    stall_event_id: int | None = None
    items: list[SaleItemCreate]
    payment: PaymentCreate | None = None


class SaleRead(BaseModel):
    id: int
    business_id: int
    customer_id: int | None
    stall_event_id: int | None
    sale_date: datetime
    currency: str
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    payment_status: str
    status: str

    model_config = ConfigDict(from_attributes=True)