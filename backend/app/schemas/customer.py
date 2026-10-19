from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CustomerCreate(BaseModel):
    business_id: int
    name: str
    phone: str | None = None
    email: str | None = None
    notes: str | None = None


class CustomerRead(BaseModel):
    id: int
    business_id: int
    name: str
    phone: str | None
    email: str | None
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)