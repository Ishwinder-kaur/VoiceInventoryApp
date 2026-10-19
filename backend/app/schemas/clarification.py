from pydantic import BaseModel


class ClarificationRequest(BaseModel):
    confirmation_id: int
    answer: str