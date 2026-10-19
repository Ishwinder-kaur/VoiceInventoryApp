from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
import os
import tempfile

from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.resolved_command import ResolvedItem, ResolvedSaleCommand
from app.services.entity_resolution import resolve_customer, resolve_product

from app.schemas.voice_command import VoiceSaleCommand
from app.schemas.voice_request import VoiceTextRequest
from app.services.llm_service import extract_sale_command

from app.schemas.confirmation import SaleConfirmation
from app.services.confirmation_service import build_sale_confirmation


from app.schemas.confirmed_sale import ConfirmedVoiceSaleRequest
from app.schemas.sale import PaymentCreate, SaleCreate, SaleItemCreate
from app.services.sale_service import create_sale

from app.models.pending_voice_command import PendingVoiceCommand

from datetime import datetime, timezone

from app.models.pending_voice_command import PendingVoiceCommand
from app.schemas.confirmation import SaleConfirmation
from app.services.speech_service import transcribe_audio
from app.schemas.clarification import ClarificationRequest

from app.services.clarification_service import (
    apply_deterministic_clarification,
)


router = APIRouter(
    prefix="/voice",
    tags=["voice"],
)

@router.post("/clarify")
async def clarify_voice_sale(
    request: ClarificationRequest,
    db: Session = Depends(get_db),
):
    pending = db.get(
        PendingVoiceCommand,
        request.confirmation_id,
    )

    if pending is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Confirmation session not found",
        )

    if pending.status not in {
        "NEEDS_CLARIFICATION",
        "PENDING_CONFIRMATION",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Cannot clarify a command with "
                f"status {pending.status}"
            ),
        )

    command = VoiceSaleCommand.model_validate(
        pending.extracted_command
    )

    clarification_text = request.answer.strip()

    #
    # FAST PATH
    #
    # First try resolving simple customer/product
    # clarifications directly from our database.
    #

    handled_without_llm = (
        apply_deterministic_clarification(
            db=db,
            business_id=pending.business_id,
            command=command,
            answer=clarification_text,
        )
    )

    combined_text = (
        f"{pending.original_text}\n"
        "Additional clarification from the owner: "
        f"{clarification_text}"
    )

    if handled_without_llm:
        extracted = command

    else:
        #
        # FALLBACK
        #
        # Complex clarification still goes to the LLM.
        #
        extracted = await extract_sale_command(
            combined_text
        )

    confirmation = build_sale_confirmation(
        db=db,
        business_id=pending.business_id,
        command=extracted,
    )

    pending.original_text = combined_text

    pending.extracted_command = (
        extracted.model_dump(
            mode="json"
        )
    )

    pending.prepared_confirmation = (
        confirmation.model_dump(
            mode="json"
        )
    )

    pending.status = (
        "PENDING_CONFIRMATION"
        if confirmation.ready_for_confirmation
        else "NEEDS_CLARIFICATION"
    )

    db.commit()
    db.refresh(pending)

    return {
        "confirmation_id": pending.id,
        "status": pending.status,
        "ready_for_confirmation": (
            confirmation.ready_for_confirmation
        ),
        "clarification_questions": (
            confirmation.clarification_questions
        ),
        "confirmation_summary": (
            confirmation.confirmation_summary
        ),
        "customer_id": confirmation.customer_id,
        "customer_name": confirmation.customer_name,
        "items": confirmation.items,
        "total": confirmation.total,
        "payment_amount": confirmation.payment_amount,
        "payment_method": confirmation.payment_method,
        "clarification_mode": (
            "DETERMINISTIC"
            if handled_without_llm
            else "LLM"
        ),
    }

@router.post("/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
):
    suffix = os.path.splitext(file.filename or "")[1]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        transcript = transcribe_audio(temp_path)

        return {
            "transcript": transcript,
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/confirm")
def confirm_voice_sale(
    request: ConfirmedVoiceSaleRequest,
    db: Session = Depends(get_db),
):
    pending = db.get(
        PendingVoiceCommand,
        request.confirmation_id,
    )

    if pending is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Confirmation session not found",
        )

    if pending.status == "CONFIRMED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This sale has already been confirmed",
        )

    if pending.status != "PENDING_CONFIRMATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sale cannot be confirmed while status is {pending.status}",
        )

    if not request.confirmed:
        pending.status = "CANCELLED"
        db.commit()

        return {
            "message": "Sale cancelled",
            "confirmation_id": pending.id,
            "status": pending.status,
        }

    confirmation = SaleConfirmation.model_validate(
        pending.prepared_confirmation
    )

    if not confirmation.ready_for_confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sale still requires clarification",
        )

    sale_items = [
        SaleItemCreate(
            product_id=item.product_id,
            quantity=item.quantity,
        )
        for item in confirmation.items
    ]

    payment = None

    if confirmation.payment_amount is not None:
        payment = PaymentCreate(
            amount=confirmation.payment_amount,
            payment_method=confirmation.payment_method,
        )

    sale_in = SaleCreate(
        business_id=pending.business_id,
        customer_id=confirmation.customer_id,
        stall_event_id=None,
        items=sale_items,
        payment=payment,
    )

    try:
        sale = create_sale(
            db=db,
            sale_in=sale_in,
        )

    except HTTPException:
        pending.status = "FAILED"
        db.commit()
        raise

    pending.status = "CONFIRMED"
    pending.confirmed_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "message": "Sale created successfully",
        "confirmation_id": pending.id,
        "sale_id": sale.id,
        "total": sale.total,
        "payment_status": sale.payment_status,
        "status": pending.status,
    }

@router.post(
    "/prepare",
    response_model=dict,
)
async def prepare_voice_sale(
    request: VoiceTextRequest,
    business_id: int,
    db: Session = Depends(get_db),
):
    extracted = await extract_sale_command(request.text)

    confirmation = build_sale_confirmation(
        db=db,
        business_id=business_id,
        command=extracted,
    )

    pending = PendingVoiceCommand(
        business_id=business_id,
        owner_id=None,
        original_text=request.text,
        extracted_command=extracted.model_dump(
            mode="json"
        ),
        prepared_confirmation=confirmation.model_dump(
            mode="json"
        ),
        status=(
            "PENDING_CONFIRMATION"
            if confirmation.ready_for_confirmation
            else "NEEDS_CLARIFICATION"
        ),
    )

    db.add(pending)
    db.commit()
    db.refresh(pending)

    return {
        "confirmation_id": pending.id,
        "status": pending.status,
        "ready_for_confirmation": confirmation.ready_for_confirmation,
        "clarification_questions": confirmation.clarification_questions,
        "confirmation_summary": confirmation.confirmation_summary,
        "customer_id": confirmation.customer_id,
        "customer_name": confirmation.customer_name,
        "items": confirmation.items,
        "total": confirmation.total,
        "payment_amount": confirmation.payment_amount,
        "payment_method": confirmation.payment_method,
    }

@router.post(
    "/resolve",
    response_model=ResolvedSaleCommand,
)
async def resolve_voice_command(
    request: VoiceTextRequest,
    business_id: int,
    db: Session = Depends(get_db),
) -> ResolvedSaleCommand:
    extracted = await extract_sale_command(request.text)

    questions = list(extracted.clarification_questions)

    customer_id = None
    customer_name = extracted.customer.name

    if customer_name:
        customer = resolve_customer(
            db=db,
            business_id=business_id,
            name=customer_name,
        )

        if customer:
            customer_id = customer.id
        else:
            questions.append(
                f"Could not find customer '{customer_name}'."
            )

    resolved_items: list[ResolvedItem] = []

    for item in extracted.items:
        product_id = None

        if item.product_name:
            product = resolve_product(
                db=db,
                business_id=business_id,
                name=item.product_name,
            )

            if product:
                product_id = product.id
            else:
                questions.append(
                    f"Could not find product '{item.product_name}'."
                )

        resolved_items.append(
            ResolvedItem(
                product_id=product_id,
                product_name=item.product_name or "",
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=item.line_total,
            )
        )

    return ResolvedSaleCommand(
        customer_id=customer_id,
        customer_name=customer_name,
        items=resolved_items,
        currency=extracted.currency,
        requires_clarification=bool(questions),
        clarification_questions=questions,
    )

@router.post(
    "/extract",
    response_model=VoiceSaleCommand,
)
async def extract_voice_command(
    request: VoiceTextRequest,
) -> VoiceSaleCommand:
    return await extract_sale_command(request.text)