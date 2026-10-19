from pydantic import BaseModel


class InventoryQueryResponse(BaseModel):
    product_id: int | None
    product_name: str | None
    quantity_on_hand: int | None

    found: bool
    answer: str