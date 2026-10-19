from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.business import Business
from app.models.customer import Customer
from app.models.inventory_movement import InventoryMovement
from app.models.payment import Payment
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.stall_event import StallEvent
from app.schemas.sale import SaleCreate


def create_sale(
    db: Session,
    sale_in: SaleCreate,
) -> Sale:
    if not sale_in.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sale must contain at least one item",
        )

    business = db.get(Business, sale_in.business_id)

    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )

    if sale_in.customer_id is not None:
        customer = db.get(Customer, sale_in.customer_id)

        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        if customer.business_id != sale_in.business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer does not belong to this business",
            )

    if sale_in.stall_event_id is not None:
        stall_event = db.get(StallEvent, sale_in.stall_event_id)

        if stall_event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stall event not found",
            )

        if stall_event.business_id != sale_in.business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stall event does not belong to this business",
            )

    subtotal = Decimal("0.00")
    prepared_items: list[tuple[Product, int, Decimal]] = []

    for item_in in sale_in.items:
        if item_in.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item quantity must be greater than zero",
            )

        product = db.get(Product, item_in.product_id)

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item_in.product_id} not found",
            )

        if product.business_id != sale_in.business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {product.id} does not belong to this business",
            )

        if not product.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {product.name} is inactive",
            )

        if product.quantity_on_hand < item_in.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for {product.name}",
            )

        line_total = product.unit_price * item_in.quantity
        subtotal += line_total

        prepared_items.append(
            (
                product,
                item_in.quantity,
                line_total,
            )
        )

    discount = Decimal("0.00")
    tax = Decimal("0.00")
    total = subtotal - discount + tax

    payment_status = "UNPAID"

    if sale_in.payment is not None:
        if sale_in.payment.amount < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount cannot be negative",
            )

        if sale_in.payment.amount > total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount cannot exceed sale total",
            )

        if sale_in.payment.amount == total:
            payment_status = "PAID"
        elif sale_in.payment.amount > 0:
            payment_status = "PARTIALLY_PAID"

    try:
        sale = Sale(
            business_id=sale_in.business_id,
            customer_id=sale_in.customer_id,
            stall_event_id=sale_in.stall_event_id,
            sale_date=datetime.now(timezone.utc),
            currency=business.default_currency,
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            total=total,
            payment_status=payment_status,
            status="CONFIRMED",
        )

        db.add(sale)
        db.flush()

        for product, quantity, line_total in prepared_items:
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.unit_price,
                line_total=line_total,
            )

            db.add(sale_item)

            product.quantity_on_hand -= quantity

            movement = InventoryMovement(
                product_id=product.id,
                sale_id=sale.id,
                movement_type="SALE",
                quantity=-quantity,
            )

            db.add(movement)

        if sale_in.payment is not None and sale_in.payment.amount > 0:
            payment = Payment(
                sale_id=sale.id,
                amount=sale_in.payment.amount,
                currency=business.default_currency,
                payment_method=sale_in.payment.payment_method,
                payment_status="COMPLETED",
                paid_at=datetime.now(timezone.utc),
            )

            db.add(payment)

        audit_event = AuditEvent(
            business_id=sale_in.business_id,
            entity_type="SALE",
            entity_id=sale.id,
            action="CREATE",
            before_data=None,
            after_data={
                "sale_id": sale.id,
                "customer_id": sale.customer_id,
                "stall_event_id": sale.stall_event_id,
                "subtotal": str(sale.subtotal),
                "discount": str(sale.discount),
                "tax": str(sale.tax),
                "total": str(sale.total),
                "payment_status": sale.payment_status,
                "status": sale.status,
                "items": [
                    {
                        "product_id": product.id,
                        "quantity": quantity,
                        "unit_price": str(product.unit_price),
                        "line_total": str(line_total),
                    }
                    for product, quantity, line_total in prepared_items
                ],
            },
            actor_type="OWNER",
            actor_id=None,
            voice_interaction_id=None,
        )

        db.add(audit_event)

        db.commit()
        db.refresh(sale)

        return sale

    except Exception:
        db.rollback()
        raise