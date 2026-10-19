from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class SaleSummaryRead(BaseModel):
    id: int
    customer_id: int | None
    customer_name: str | None
    sale_date: datetime

    total: Decimal
    currency: str

    payment_status: str
    status: str

    item_count: int