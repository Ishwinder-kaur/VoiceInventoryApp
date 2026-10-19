from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.assistant_intent import AssistantIntent
from app.schemas.inventory_query import InventoryQueryResponse
from app.schemas.voice_request import VoiceTextRequest
from app.services.intent_service import classify_intent
from app.services.inventory_query_service import check_inventory


router = APIRouter(
    prefix="/assistant",
    tags=["assistant"],
)


@router.post(
    "/intent",
    response_model=AssistantIntent,
)
async def detect_intent(
    request: VoiceTextRequest,
) -> AssistantIntent:
    return await classify_intent(
        request.text
    )


@router.post(
    "/inventory",
    response_model=InventoryQueryResponse,
)
def query_inventory(
    request: VoiceTextRequest,
    business_id: int,
    db: Session = Depends(get_db),
) -> InventoryQueryResponse:
    return check_inventory(
        db=db,
        business_id=business_id,
        text=request.text,
    )