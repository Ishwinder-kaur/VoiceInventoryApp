from sqlalchemy.orm import Session

from app.schemas.voice_command import VoiceSaleCommand
from app.services.entity_resolution import (
    resolve_customer,
    resolve_customer_from_phrase,
    resolve_product,
    resolve_product_from_phrase,
)


def apply_deterministic_clarification(
    db: Session,
    business_id: int,
    command: VoiceSaleCommand,
    answer: str,
) -> bool:
    """
    Attempt to apply a simple clarification without calling the LLM.

    Returns True if we safely changed the command.
    Returns False when the clarification should fall back to the LLM.
    """

    changed = False

    #
    # CUSTOMER
    #

    customer_needs_resolution = False

    if not command.customer.name:
        customer_needs_resolution = True
    else:
        current_customer = resolve_customer(
            db=db,
            business_id=business_id,
            name=command.customer.name,
        )

        if current_customer is None:
            customer_needs_resolution = True

    if customer_needs_resolution:
        customer = resolve_customer_from_phrase(
            db=db,
            business_id=business_id,
            phrase=answer,
        )

        if customer is not None:
            command.customer.name = customer.name
            command.customer.state = "PROVIDED"
            changed = True

    #
    # PRODUCTS
    #

    unresolved_item_indexes: list[int] = []

    for index, item in enumerate(command.items):
        if not item.product_name:
            unresolved_item_indexes.append(index)
            continue

        existing_product = resolve_product(
            db=db,
            business_id=business_id,
            name=item.product_name,
        )

        if existing_product is None:
            unresolved_item_indexes.append(index)

    # Only automatically replace a product when exactly
    # one item currently needs product clarification.
    if len(unresolved_item_indexes) == 1:
        product = resolve_product_from_phrase(
            db=db,
            business_id=business_id,
            phrase=answer,
        )

        if product is not None:
            item = command.items[
                unresolved_item_indexes[0]
            ]

            item.product_name = product.name
            item.product_state = "PROVIDED"

            changed = True

    return changed