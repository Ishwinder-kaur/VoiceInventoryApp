from typing import Literal

from pydantic import BaseModel, Field


AssistantIntentName = Literal[
    "CREATE_SALE",
    "CHECK_INVENTORY",
    "GET_CUSTOMER_INFO",
    "GET_CUSTOMER_PURCHASE_HISTORY",
    "GET_SALE_DETAILS",
    "GET_TODAY_SALES",
    "GET_EVENT_SALES",
    "GET_REVENUE_SUMMARY",
    "UNKNOWN",
]


class AssistantIntent(BaseModel):
    intent: AssistantIntentName
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )