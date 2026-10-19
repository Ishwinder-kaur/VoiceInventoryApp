from app.schemas.voice_command import VoiceSaleCommand


command = VoiceSaleCommand.model_validate(
    {
        "intent": "CREATE_SALE",
        "customer": {
            "name": "ABC",
            "state": "PROVIDED",
        },
        "items": [
            {
                "product_name": "ceramic cup set",
                "quantity": 2,
                "unit_price": 30,
                "line_total": 60,
                "product_state": "PROVIDED",
                "quantity_state": "PROVIDED",
                "price_state": "PROVIDED",
            }
        ],
        "currency": "USD",
        "currency_state": "INFERRED",
        "payment": {
            "amount": 60,
            "payment_method": "CARD",
            "payment_status": "PAID",
            "amount_state": "PROVIDED",
            "method_state": "PROVIDED",
        },
        "stall_event_name": None,
        "stall_event_state": "MISSING",
        "requires_clarification": False,
        "clarification_questions": [],
    }
)

print(command.model_dump_json(indent=2))