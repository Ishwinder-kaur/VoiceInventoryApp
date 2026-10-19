from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.audit_event import AuditEvent
from app.schemas.audit import AuditEventRead


router = APIRouter(
    prefix="/audit",
    tags=["audit"],
)


@router.get(
    "",
    response_model=list[AuditEventRead],
)
def list_audit_events(
    business_id: int,
    entity_type: str | None = None,
    entity_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[AuditEvent]:
    stmt = select(AuditEvent).where(
        AuditEvent.business_id == business_id
    )

    if entity_type:
        stmt = stmt.where(
            AuditEvent.entity_type == entity_type
        )

    if entity_id is not None:
        stmt = stmt.where(
            AuditEvent.entity_id == entity_id
        )

    stmt = stmt.order_by(
        AuditEvent.created_at.desc()
    )

    return list(db.scalars(stmt).all())