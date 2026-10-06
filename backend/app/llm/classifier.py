import json
from typing import Any

import httpx

from app.core.config import settings
from app.services import router


def llm_enabled() -> bool:
    return bool(settings.llm_base_url and settings.llm_model)


def classify_with_llm(question: str, known: dict[str, set[str]]) -> tuple[str, dict[str, Any]]:
    if not llm_enabled():
        return "UNKNOWN", {}

    symbols = sorted(known.get("symbols", []))
    sectors = sorted(known.get("sectors", []))
    customers = sorted(known.get("customer_names", []))

    system = (
        "You classify portfolio graph questions. Reply with JSON only: "
        '{"intent":"...", "entities":{"symbol":null,"symbols":[],"sector":null,'
        '"change_percent":null,"customer_name":null,"customer_id":null}}. '
        f"Intents: STOCK_HOLDERS, MULTI_STOCK_HOLDERS, SECTOR_EXPOSURE, STOCK_IMPACT, "
        f"SECTOR_IMPACT, CUSTOMER_EXPOSURE, UNKNOWN. "
        f"Symbols: {symbols}. Sectors: {sectors}. Customers: {customers[:20]}..."
    )
    try:
        url = settings.llm_base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"} if settings.llm_api_key else {}
        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
            "temperature": 0,
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            intent = data.get("intent", "UNKNOWN")
            entities = data.get("entities") or {}
            if intent == "UNKNOWN":
                return "UNKNOWN", {}
            return intent, entities
    except Exception:
        return "UNKNOWN", {}
