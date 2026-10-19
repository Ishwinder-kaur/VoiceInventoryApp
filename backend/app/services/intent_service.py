import json
import re

import httpx

from app.schemas.assistant_intent import AssistantIntent


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen3:4b"


INTENT_SYSTEM_PROMPT = """
You classify commands for a small retail inventory and sales application.

Choose exactly one intent from:

CREATE_SALE
CHECK_INVENTORY
GET_CUSTOMER_INFO
GET_CUSTOMER_PURCHASE_HISTORY
GET_SALE_DETAILS
GET_TODAY_SALES
GET_EVENT_SALES
GET_REVENUE_SUMMARY
UNKNOWN

Examples:

"ABC bought two ceramic cup sets for sixty dollars."
-> CREATE_SALE

"How many ceramic cup sets do I have left?"
-> CHECK_INVENTORY

"What is the stock of ceramic cup sets?"
-> CHECK_INVENTORY

"What did ABC buy last time?"
-> GET_CUSTOMER_PURCHASE_HISTORY

"Show me ABC's purchase history."
-> GET_CUSTOMER_PURCHASE_HISTORY

"How much did I sell today?"
-> GET_TODAY_SALES

"What is today's revenue?"
-> GET_REVENUE_SUMMARY

"Show me sale number 12."
-> GET_SALE_DETAILS

Rules:

1. Return exactly one intent.
2. confidence must be between 0 and 1.
3. Use UNKNOWN only when no supported intent fits.
4. Return structured JSON only.
"""


def classify_intent_deterministically(
    text: str,
) -> AssistantIntent | None:
    normalized = text.lower().strip()

    #
    # CHECK INVENTORY
    #

    inventory_patterns = [
        r"\bhow many\b.*\b(left|available|in stock)\b",
        r"\bwhat(?:'s| is) (?:the )?stock\b",
        r"\bcheck (?:the )?stock\b",
        r"\binventory (?:for|of)\b",
        r"\bhow much stock\b",
        r"\bdo i have left\b",
    ]

    for pattern in inventory_patterns:
        if re.search(pattern, normalized):
            return AssistantIntent(
                intent="CHECK_INVENTORY",
                confidence=1.0,
            )

    #
    # CUSTOMER PURCHASE HISTORY
    #

    customer_history_patterns = [
        r"\bwhat did\b.*\bbuy\b",
        r"\bwhat has\b.*\bbought\b",
        r"\bpurchase history\b",
        r"\bbuy last time\b",
        r"\bbought last time\b",
        r"\blast purchase\b",
    ]

    for pattern in customer_history_patterns:
        if re.search(pattern, normalized):
            return AssistantIntent(
                intent="GET_CUSTOMER_PURCHASE_HISTORY",
                confidence=1.0,
            )

    #
    # TODAY'S SALES
    #

    today_sales_patterns = [
        r"\bsales today\b",
        r"\btoday'?s sales\b",
        r"\bhow many sales\b.*\btoday\b",
    ]

    for pattern in today_sales_patterns:
        if re.search(pattern, normalized):
            return AssistantIntent(
                intent="GET_TODAY_SALES",
                confidence=1.0,
            )

    #
    # REVENUE
    #

    revenue_patterns = [
        r"\brevenue\b",
        r"\bhow much did i sell\b",
        r"\bsales total\b",
        r"\btotal sales amount\b",
    ]

    for pattern in revenue_patterns:
        if re.search(pattern, normalized):
            return AssistantIntent(
                intent="GET_REVENUE_SUMMARY",
                confidence=1.0,
            )

    #
    # SPECIFIC SALE DETAILS
    #

    if re.search(
        r"\b(sale|transaction)\s*(number|#)?\s*\d+\b",
        normalized,
    ):
        return AssistantIntent(
            intent="GET_SALE_DETAILS",
            confidence=1.0,
        )

    #
    # CREATE SALE
    #
    # Common verbs used when recording a purchase.
    #

    sale_patterns = [
        r"\bbought\b",
        r"\bpurchased\b",
        r"\bbuying\b",
        r"\bsold\b",
    ]

    for pattern in sale_patterns:
        if re.search(pattern, normalized):
            return AssistantIntent(
                intent="CREATE_SALE",
                confidence=0.95,
            )

    return None


async def classify_intent(
    text: str,
) -> AssistantIntent:
    deterministic_result = (
        classify_intent_deterministically(text)
    )

    if deterministic_result is not None:
        return deterministic_result

    schema = AssistantIntent.model_json_schema()

    payload = {
        "model": MODEL_NAME,
        "stream": False,
        "think": False,
        "keep_alive": "30m",
        "format": schema,
        "messages": [
            {
                "role": "system",
                "content": INTENT_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        "options": {
            "temperature": 0,
            "num_predict": 100,
        },
    }

    timeout = httpx.Timeout(
        connect=10.0,
        read=300.0,
        write=30.0,
        pool=10.0,
    )

    async with httpx.AsyncClient(
        timeout=timeout
    ) as client:
        response = await client.post(
            OLLAMA_URL,
            json=payload,
        )

        response.raise_for_status()

    data = response.json()

    content = data["message"]["content"]

    parsed = json.loads(content)

    return AssistantIntent.model_validate(parsed)