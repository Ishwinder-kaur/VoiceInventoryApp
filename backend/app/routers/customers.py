from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import get_db
from app.models.business import Business
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerRead
from app.models.customer_alias import CustomerAlias
from app.schemas.alias import AliasCreate, CustomerAliasRead


router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)

@router.post(
    "/{customer_id}/aliases",
    response_model=CustomerAliasRead,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_alias(
    customer_id: int,
    alias_in: AliasCreate,
    db: Session = Depends(get_db),
) -> CustomerAlias:
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    alias = CustomerAlias(
        customer_id=customer_id,
        alias=alias_in.alias.strip(),
    )

    db.add(alias)
    db.commit()
    db.refresh(alias)

    return alias

@router.post(
    "",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_db),
) -> Customer:
    business = db.get(Business, customer_in.business_id)

    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )

    customer = Customer(
        business_id=customer_in.business_id,
        name=customer_in.name,
        phone=customer_in.phone,
        email=customer_in.email,
        notes=customer_in.notes,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer

@router.get(
    "",
    response_model=list[CustomerRead],
)
def list_customers(
    business_id: int,
    query: str | None = None,
    db: Session = Depends(get_db),
) -> list[Customer]:
    stmt = select(Customer).where(
        Customer.business_id == business_id
    )

    if query:
        stmt = (
            stmt.outerjoin(
                CustomerAlias,
                CustomerAlias.customer_id == Customer.id,
            )
            .where(
                Customer.name.ilike(f"%{query}%")
                | CustomerAlias.alias.ilike(f"%{query}%")
            )
            .distinct()
        )

    stmt = stmt.order_by(Customer.name)

    return list(db.scalars(stmt).all())

@router.get(
    "/{customer_id}",
    response_model=CustomerRead,
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
) -> Customer:
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    return customer