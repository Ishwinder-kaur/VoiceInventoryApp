from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.business import Business
from app.schemas.business import BusinessCreate, BusinessRead


router = APIRouter(
    prefix="/businesses",
    tags=["businesses"],
)


@router.post(
    "",
    response_model=BusinessRead,
    status_code=status.HTTP_201_CREATED,
)
def create_business(
    business_in: BusinessCreate,
    db: Session = Depends(get_db),
) -> Business:
    business = Business(
        name=business_in.name,
        default_currency=business_in.default_currency,
        timezone=business_in.timezone,
    )

    db.add(business)
    db.commit()
    db.refresh(business)

    return business


@router.get(
    "/{business_id}",
    response_model=BusinessRead,
)
def get_business(
    business_id: int,
    db: Session = Depends(get_db),
) -> Business:
    business = db.get(Business, business_id)

    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )

    return business