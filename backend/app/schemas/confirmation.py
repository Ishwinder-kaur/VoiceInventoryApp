from decimal import Decimal

from pydantic import BaseModel


class ConfirmationItem(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class SaleConfirmation(BaseModel):
    customer_id: int | None
    customer_name: str | None

    items: list[ConfirmationItem]

    total: Decimal

    payment_amount: Decimal | None
    payment_method: str | None

    ready_for_confirmation: bool
    clarification_questions: list[str]

    confirmation_summary: str