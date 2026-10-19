import json
from socket import timeout
import re

import httpx

from app.schemas.voice_command import VoiceSaleCommand


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen3:4b"


SYSTEM_PROMPT = """
You are an extraction engine for a voice inventory application.

Convert a natural-language sales statement into structured JSON.

Rules:

1. Never invent customer names, products, quantities, prices,
   payment methods, or payment facts.

2. If information is explicitly stated, mark it PROVIDED.

3. If information is missing, mark it MISSING.

4. If information is ambiguous, mark it AMBIGUOUS.

5. If a safe logical inference is made, mark it INFERRED.

6. The intent must be CREATE_SALE.

7. Carefully extract payment information.

Payment rules:

- "paid by card", "paid with card", "card payment"
  means:
    payment_method = "CARD"
    payment_status = "PAID"

- "paid cash", "paid by cash", "paid in cash"
  means:
    payment_method = "CASH"
    payment_status = "PAID"

- If the customer clearly paid the entire sale,
  set payment_status = "PAID".

- If the sale total is explicitly known and the customer clearly
  paid in full, use the sale total as the payment amount.

- If the payment method is stated but the amount is not explicitly
  stated, payment amount may remain null. The application will
  calculate it safely later.

8. If required information cannot be safely determined,
   set requires_clarification=true.

9. Add concise clarification questions for genuinely missing or
   ambiguous information.

10. Return JSON only.
"""

def normalize_payment_from_text(
    text: str,
    command: VoiceSaleCommand,
) -> VoiceSaleCommand:
    normalized = text.lower().strip()

    card_paid = re.search(
        r"\b(paid\s+(by|with)\s+card|card\s+payment)\b",
        normalized,
    )

    cash_paid = re.search(
        r"\b(paid\s+(by|in)\s+cash|paid\s+cash|cash\s+payment)\b",
        normalized,
    )

    if card_paid:
        if command.payment is None:
            from app.schemas.voice_command import ExtractedPayment

            command.payment = ExtractedPayment()

        command.payment.payment_method = "CARD"
        command.payment.payment_status = "PAID"
        command.payment.method_state = "PROVIDED"

    elif cash_paid:
        if command.payment is None:
            from app.schemas.voice_command import ExtractedPayment

            command.payment = ExtractedPayment()

        command.payment.payment_method = "CASH"
        command.payment.payment_status = "PAID"
        command.payment.method_state = "PROVIDED"

    return command


async def extract_sale_command(
    text: str,
) -> VoiceSaleCommand:
    schema = VoiceSaleCommand.model_json_schema()

    payload = {
        "model": MODEL_NAME,
        "stream": False,
        "think": False,
        "keep_alive": "30m",
        "format": schema,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        "options": {
            "temperature": 0,
        },
    }

    timeout = httpx.Timeout(
        connect=10.0,
        read=600.0,
        write=30.0,
        pool=10.0,
    )   

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            OLLAMA_URL,
            json=payload,
        )

        response.raise_for_status()

    data = response.json()

    content = data["message"]["content"]

    parsed = json.loads(content)

    command = VoiceSaleCommand.model_validate(parsed)

    command = normalize_payment_from_text(
        text=text,
        command=command,
    )

    return command