from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import get_db
from app.models.business import Business
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductRead
from app.models.product_alias import ProductAlias
from app.schemas.alias import AliasCreate, ProductAliasRead


router = APIRouter(
    prefix="/products",
    tags=["products"],
)

@router.post(
    "/{product_id}/aliases",
    response_model=ProductAliasRead,
    status_code=status.HTTP_201_CREATED,
)
def create_product_alias(
    product_id: int,
    alias_in: AliasCreate,
    db: Session = Depends(get_db),
) -> ProductAlias:
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    alias = ProductAlias(
        product_id=product_id,
        alias=alias_in.alias.strip(),
    )

    db.add(alias)
    db.commit()
    db.refresh(alias)

    return alias

@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
) -> Product:
    business = db.get(Business, product_in.business_id)

    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )

    product = Product(
        business_id=product_in.business_id,
        sku=product_in.sku,
        name=product_in.name,
        unit_price=product_in.unit_price,
        currency=product_in.currency,
        active=product_in.active,
        quantity_on_hand=product_in.quantity_on_hand,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product

@router.get(
    "",
    response_model=list[ProductRead],
)
def list_products(
    business_id: int,
    query: str | None = None,
    db: Session = Depends(get_db),
) -> list[Product]:
    stmt = select(Product).where(
        Product.business_id == business_id
    )

    if query:
        stmt = (
            stmt.outerjoin(
                ProductAlias,
                ProductAlias.product_id == Product.id,
            )
            .where(
                Product.name.ilike(f"%{query}%")
                | ProductAlias.alias.ilike(f"%{query}%")
            )
            .distinct()
        )

    stmt = stmt.order_by(Product.name)

    return list(db.scalars(stmt).all())

@router.get(
    "/{product_id}",
    response_model=ProductRead,
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
) -> Product:
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product