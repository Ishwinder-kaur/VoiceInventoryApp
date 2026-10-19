from sqlalchemy.orm import Session

from app.schemas.inventory_query import InventoryQueryResponse
from app.services.entity_resolution import (
    resolve_product,
    resolve_product_from_phrase,
)


def check_inventory(
    db: Session,
    business_id: int,
    text: str,
) -> InventoryQueryResponse:
    product = resolve_product(
        db=db,
        business_id=business_id,
        name=text,
    )

    if product is None:
        product = resolve_product_from_phrase(
            db=db,
            business_id=business_id,
            phrase=text,
        )

    if product is None:
        return InventoryQueryResponse(
            product_id=None,
            product_name=None,
            quantity_on_hand=None,
            found=False,
            answer=(
                "I could not determine which product you meant."
            ),
        )

    return InventoryQueryResponse(
        product_id=product.id,
        product_name=product.name,
        quantity_on_hand=product.quantity_on_hand,
        found=True,
        answer=(
            f"You have {product.quantity_on_hand} "
            f"{product.name} in stock."
        ),
    )