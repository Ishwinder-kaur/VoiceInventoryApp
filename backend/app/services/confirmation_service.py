from decimal import Decimal

from sqlalchemy.orm import Session

from app.schemas.confirmation import (
    ConfirmationItem,
    SaleConfirmation,
)
from app.schemas.voice_command import VoiceSaleCommand
from app.services.entity_resolution import (
    resolve_customer,
    resolve_product,
)


def build_sale_confirmation(
    db: Session,
    business_id: int,
    command: VoiceSaleCommand,
) -> SaleConfirmation:
    questions: list[str] = []

    customer_id = None
    customer_name = command.customer.name

    if customer_name:
        customer = resolve_customer(
            db=db,
            business_id=business_id,
            name=customer_name,
        )

        if customer:
            customer_id = customer.id
            customer_name = customer.name
        else:
            questions.append(
                f"Which customer did you mean by '{customer_name}'?"
            )

    else:
        questions.append(
            "Which customer made this purchase?"
        )

    confirmation_items: list[ConfirmationItem] = []
    total = Decimal("0.00")

    for item in command.items:
        if not item.product_name:
            questions.append(
                "Which product was purchased?"
            )
            continue

        product = resolve_product(
            db=db,
            business_id=business_id,
            name=item.product_name,
        )

        if product is None:
            questions.append(
                f"Which product did you mean by '{item.product_name}'?"
            )
            continue

        if item.quantity is None or item.quantity <= 0:
            questions.append(
                f"How many {product.name} were purchased?"
            )
            continue

        unit_price = product.unit_price
        line_total = unit_price * item.quantity

        confirmation_items.append(
            ConfirmationItem(
                product_id=product.id,
                product_name=product.name,
                quantity=item.quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )

        total += line_total

    payment_amount = None
    payment_method = None

    if command.payment:
        payment_amount = command.payment.amount
        payment_method = command.payment.payment_method

        # If the owner explicitly said the sale was paid in full,
        # use our deterministic calculated total rather than asking
        # the LLM to calculate the payment amount.
        if (
            command.payment.payment_status == "PAID"
            and payment_amount is None
        ):
            payment_amount = total

    if payment_amount is not None and payment_amount != total:
        questions.append(
            f"The payment amount is {payment_amount}, "
            f"but the calculated sale total is {total}. "
            "Please confirm the correct amount."
        )

    ready = len(questions) == 0

    if ready:
        item_text = ", ".join(
            f"{item.quantity} x {item.product_name}"
            for item in confirmation_items
        )

        confirmation_summary = (
            f"{customer_name} is buying {item_text} "
            f"for a total of ${total}"
        )

        if payment_method:
            confirmation_summary += (
                f", paid by {payment_method}"
            )

        confirmation_summary += ". Confirm?"
    else:
        confirmation_summary = (
            "More information is required before this sale can be confirmed."
        )

    return SaleConfirmation(
        customer_id=customer_id,
        customer_name=customer_name,
        items=confirmation_items,
        total=total,
        payment_amount=payment_amount,
        payment_method=payment_method,
        ready_for_confirmation=ready,
        clarification_questions=questions,
        confirmation_summary=confirmation_summary,
    )