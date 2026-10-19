from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class SaleItemRead(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class PaymentRead(BaseModel):
    id: int
    amount: Decimal
    currency: str
    payment_method: str | None
    payment_status: str
    paid_at: datetime | None


class InventoryMovementRead(BaseModel):
    id: int
    product_id: int
    product_name: str
    movement_type: str
    quantity: int
    created_at: datetime


class SaleDetailRead(BaseModel):
    id: int
    business_id: int

    customer_id: int | None
    customer_name: str | None

    stall_event_id: int | None

    sale_date: datetime

    currency: str

    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal

    payment_status: str
    status: str

    items: list[SaleItemRead]
    payments: list[PaymentRead]
    inventory_movements: list[InventoryMovementRead]