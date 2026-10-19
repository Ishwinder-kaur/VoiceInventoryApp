from decimal import Decimal

from pydantic import BaseModel


class ResolvedItem(BaseModel):
    product_id: int | None
    product_name: str
    quantity: int | None
    unit_price: Decimal | None
    line_total: Decimal | None


class ResolvedSaleCommand(BaseModel):
    customer_id: int | None
    customer_name: str | None

    items: list[ResolvedItem]

    currency: str | None

    requires_clarification: bool
    clarification_questions: list[str]