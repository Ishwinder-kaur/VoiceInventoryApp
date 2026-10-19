from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db

from app.models.customer import Customer
from app.models.inventory_movement import InventoryMovement
from app.models.payment import Payment
from app.models.product import Product
from app.models.sale import Sale
from app.models.sale_item import SaleItem

from app.schemas.sale import SaleCreate, SaleRead
from app.schemas.sale_detail import SaleDetailRead
from app.schemas.sale_summary import SaleSummaryRead

from app.services.sale_service import create_sale


router = APIRouter(
    prefix="/sales",
    tags=["sales"],
)


@router.post(
    "",
    response_model=SaleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_sale_endpoint(
    sale_in: SaleCreate,
    db: Session = Depends(get_db),
):
    return create_sale(
        db=db,
        sale_in=sale_in,
    )


@router.get(
    "",
    response_model=list[SaleSummaryRead],
)
def list_sales(
    business_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    if limit < 1:
        limit = 1

    if limit > 100:
        limit = 100

    item_count_subquery = (
        select(
            SaleItem.sale_id,
            func.sum(SaleItem.quantity).label(
                "item_count"
            ),
        )
        .group_by(SaleItem.sale_id)
        .subquery()
    )

    stmt = (
        select(
            Sale,
            Customer.name.label(
                "customer_name"
            ),
            func.coalesce(
                item_count_subquery.c.item_count,
                0,
            ).label(
                "item_count"
            ),
        )
        .outerjoin(
            Customer,
            Customer.id == Sale.customer_id,
        )
        .outerjoin(
            item_count_subquery,
            item_count_subquery.c.sale_id
            == Sale.id,
        )
        .where(
            Sale.business_id == business_id
        )
        .order_by(
            Sale.sale_date.desc(),
            Sale.id.desc(),
        )
        .limit(limit)
    )

    rows = db.execute(stmt).all()

    return [
        SaleSummaryRead(
            id=sale.id,
            customer_id=sale.customer_id,
            customer_name=customer_name,
            sale_date=sale.sale_date,
            total=sale.total,
            currency=sale.currency,
            payment_status=sale.payment_status,
            status=sale.status,
            item_count=int(item_count or 0),
        )
        for sale, customer_name, item_count in rows
    ]


@router.get(
    "/{sale_id}",
    response_model=SaleDetailRead,
)
def get_sale_detail(
    sale_id: int,
    db: Session = Depends(get_db),
):
    sale = db.get(
        Sale,
        sale_id,
    )

    if sale is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found",
        )

    customer_name = None

    if sale.customer_id is not None:
        customer = db.get(
            Customer,
            sale.customer_id,
        )

        if customer is not None:
            customer_name = customer.name

    item_rows = db.execute(
        select(
            SaleItem,
            Product.name.label(
                "product_name"
            ),
        )
        .join(
            Product,
            Product.id == SaleItem.product_id,
        )
        .where(
            SaleItem.sale_id == sale_id
        )
    ).all()

    payment_rows = list(
        db.scalars(
            select(Payment).where(
                Payment.sale_id == sale_id
            )
        ).all()
    )

    movement_rows = db.execute(
        select(
            InventoryMovement,
            Product.name.label(
                "product_name"
            ),
        )
        .join(
            Product,
            Product.id
            == InventoryMovement.product_id,
        )
        .where(
            InventoryMovement.sale_id
            == sale_id
        )
    ).all()

    items = [
        {
            "id": item.id,
            "product_id": item.product_id,
            "product_name": product_name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "line_total": item.line_total,
        }
        for item, product_name in item_rows
    ]

    inventory_movements = [
        {
            "id": movement.id,
            "product_id": movement.product_id,
            "product_name": product_name,
            "movement_type": movement.movement_type,
            "quantity": movement.quantity,
            "created_at": movement.created_at,
        }
        for movement, product_name in movement_rows
    ]

    return {
        "id": sale.id,
        "business_id": sale.business_id,

        "customer_id": sale.customer_id,
        "customer_name": customer_name,

        "stall_event_id": sale.stall_event_id,

        "sale_date": sale.sale_date,

        "currency": sale.currency,

        "subtotal": sale.subtotal,
        "discount": sale.discount,
        "tax": sale.tax,
        "total": sale.total,

        "payment_status": sale.payment_status,
        "status": sale.status,

        "items": items,
        "payments": payment_rows,
        "inventory_movements": inventory_movements,
    }