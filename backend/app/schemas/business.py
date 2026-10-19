from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BusinessCreate(BaseModel):
    name: str
    default_currency: str = "USD"
    timezone: str = "America/New_York"


class BusinessRead(BaseModel):
    id: int
    name: str
    default_currency: str
    timezone: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)