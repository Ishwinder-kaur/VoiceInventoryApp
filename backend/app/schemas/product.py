from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    business_id: int
    sku: str | None = None
    name: str
    unit_price: Decimal
    currency: str = "USD"
    active: bool = True
    quantity_on_hand: int = 0


class ProductRead(BaseModel):
    id: int
    business_id: int
    sku: str | None
    name: str
    unit_price: Decimal
    quantity_on_hand: int
    currency: str
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)