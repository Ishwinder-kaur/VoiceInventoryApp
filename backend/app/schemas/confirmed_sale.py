from pydantic import BaseModel


class ConfirmedVoiceSaleRequest(BaseModel):
    confirmation_id: int
    confirmed: bool