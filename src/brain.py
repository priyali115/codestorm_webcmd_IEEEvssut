"""Gemini-powered intent classification for the universal agent."""

import json
from typing import Any

from google import genai
from google.genai import types
from src.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"
ALLOWED_MODULES = {
    "student_opportunities",
    "recruitment",
    "bills",
    "healthcare",
}

SYSTEM_INSTRUCTION = """You are the router for a Universal AI Browser Agent.
Classify the user query into exactly one of these modules:
student_opportunities, recruitment, bills, or healthcare.
Extract the main target, such as a job title, bill type, opportunity type, or medical specialty.
Return exactly one JSON object with exactly these keys and no additional keys:
{"module": "...", "target": "..."}
Use an empty string for target when no target is specified."""


def analyze_and_route_intent(user_prompt: str) -> dict:
    """Classify a user query with Gemini and return its module and target."""
    if not user_prompt or not user_prompt.strip():
        raise ValueError("user_prompt must not be empty")

    chat = client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
        ),
    )
    response = chat.send_message(user_prompt.strip())

    try:
        result: Any = json.loads(response.text or "")
    except json.JSONDecodeError as exc:
        raise RuntimeError("Gemini returned invalid JSON for the intent") from exc

    if (
        not isinstance(result, dict)
        or set(result) != {"module", "target"}
        or result["module"] not in ALLOWED_MODULES
        or not isinstance(result["target"], str)
    ):
        raise RuntimeError("Gemini returned an invalid intent shape")
    return {"module": result["module"], "target": result["target"]}