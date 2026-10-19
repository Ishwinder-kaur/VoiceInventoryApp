from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditEventRead(BaseModel):
    id: int
    business_id: int
    entity_type: str
    entity_id: int | None
    action: str
    before_data: dict | None
    after_data: dict | None
    actor_type: str
    actor_id: int | None
    voice_interaction_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)