from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


FieldState = Literal[
    "PROVIDED",
    "INFERRED",
    "MISSING",
    "AMBIGUOUS",
]


class ExtractedCustomer(BaseModel):
    name: str | None = None
    state: FieldState = "MISSING"


class ExtractedSaleItem(BaseModel):
    product_name: str | None = None
    quantity: int | None = None
    unit_price: Decimal | None = None
    line_total: Decimal | None = None

    product_state: FieldState = "MISSING"
    quantity_state: FieldState = "MISSING"
    price_state: FieldState = "MISSING"


class ExtractedPayment(BaseModel):
    amount: Decimal | None = None
    payment_method: str | None = None
    payment_status: Literal[
        "PAID",
        "PARTIALLY_PAID",
        "UNPAID",
        "UNKNOWN",
    ] = "UNKNOWN"

    amount_state: FieldState = "MISSING"
    method_state: FieldState = "MISSING"


class VoiceSaleCommand(BaseModel):
    intent: Literal["CREATE_SALE"]

    customer: ExtractedCustomer

    items: list[ExtractedSaleItem] = Field(
        default_factory=list
    )

    currency: str | None = None
    currency_state: FieldState = "MISSING"

    payment: ExtractedPayment | None = None

    stall_event_name: str | None = None
    stall_event_state: FieldState = "MISSING"

    requires_clarification: bool = False

    clarification_questions: list[str] = Field(
        default_factory=list
    )