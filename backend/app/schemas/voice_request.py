from pydantic import BaseModel


class VoiceTextRequest(BaseModel):
    text: str