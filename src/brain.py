"""Gemini-powered intent classification and argument extraction for the Universal AI Browser Agent."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

# Ensure project root is in sys.path for direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from google import genai
from google.genai import types
from src.config import GEMINI_API_KEY, GEMINI_MODEL

ALLOWED_MODULES = {
    "student_opportunities",
    "recruitment",
    "bills",
    "healthcare",
}

SYSTEM_INSTRUCTION = """You are the intelligent router for a Universal AI Browser Agent.
Analyze the user query and output a structured JSON intent for one of the 4 supported modules:

1. "student_opportunities": Scholarships, internships, hackathons, academic opportunities, research grants, skill-matching contests.
2. "recruitment": Job listings, candidate matching, resume collection, recruitment screening, active hiring posts.
3. "bills": Electricity, broadband/internet, mobile recharge, utility balances, bill payments.
4. "healthcare": Clinic booking, specialist search, doctor availability, appointment reservations.

Return EXACTLY ONE valid JSON object matching this schema:
{
  "module": "student_opportunities" | "recruitment" | "bills" | "healthcare",
  "target": "main search target or provider name",
  "action": "search" | "apply" | "status" | "pay" | "find_slots" | "book_appointment",
  "requires_confirmation": true | false,
  "parameters": {}
}

Rules:
- "requires_confirmation" MUST be true for high-impact actions like paying bills ("pay"), finalizing clinic appointments ("book_appointment"), or submitting official job applications ("apply").
- "requires_confirmation" SHOULD be false for read-only actions like checking balances ("status"), searching slots ("find_slots"), or listing scholarships ("search").
- Use empty string or default values if parameters are omitted.
"""


def _get_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment or project .env file.")
    return genai.Client(api_key=GEMINI_API_KEY)


def analyze_and_route_intent(user_prompt: str) -> dict[str, Any]:
    """Classify user query using Google Gemini API and return structured intent dict."""
    if not user_prompt or not user_prompt.strip():
        raise ValueError("user_prompt must not be empty")

    client = _get_client()
    model_to_use = GEMINI_MODEL or "gemini-3.6-flash"

    # Fallback model list
    candidate_models = [model_to_use, "gemini-3.6-flash", "gemini-2.5-flash", "gemini-2.0-flash"]
    # Remove duplicates while preserving order
    seen = set()
    models = [m for m in candidate_models if not (m in seen or seen.add(m))]

    last_error = None
    response_text = None

    for model_name in models:
        try:
            chat = client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )
            response = chat.send_message(user_prompt.strip())
            response_text = response.text
            if response_text:
                break
        except Exception as exc:
            last_error = exc
            continue

    if not response_text:
        # Local heuristic fallback if network/API fails
        return _fallback_rule_based_intent(user_prompt, last_error)

    try:
        result: Any = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Gemini returned non-JSON response: {response_text}") from exc

    if not isinstance(result, dict) or "module" not in result:
        raise RuntimeError("Gemini returned invalid intent structure")

    module = result.get("module")
    if module not in ALLOWED_MODULES:
        module = _fallback_module_matching(user_prompt)

    target = str(result.get("target", "") or "")
    action = str(result.get("action", "search") or "search")
    requires_confirmation = bool(result.get("requires_confirmation", False))
    parameters = result.get("parameters", {}) if isinstance(result.get("parameters"), dict) else {}

    # Enforce confirmation rules
    if action in {"pay", "book_appointment", "apply"} or "pay" in user_prompt.lower() or "book" in user_prompt.lower():
        requires_confirmation = True

    return {
        "module": module,
        "target": target,
        "action": action,
        "requires_confirmation": requires_confirmation,
        "parameters": parameters,
    }


def _fallback_module_matching(prompt: str) -> str:
    prompt_lower = prompt.lower()
    if any(w in prompt_lower for w in ["bill", "electricity", "broadband", "internet", "mobile", "recharge", "pay", "due"]):
        return "bills"
    if any(w in prompt_lower for w in ["doctor", "clinic", "hospital", "health", "appointment", "specialist", "dentist", "cardio"]):
        return "healthcare"
    if any(w in prompt_lower for w in ["job", "recruitment", "hire", "candidate", "resume", "applicant", "vacancy"]):
        return "recruitment"
    return "student_opportunities"


def _fallback_rule_based_intent(prompt: str, error: Exception | None = None) -> dict[str, Any]:
    module = _fallback_module_matching(prompt)
    prompt_lower = prompt.lower()
    
    action = "search"
    requires_confirmation = False

    if module == "bills":
        if "pay" in prompt_lower:
            action = "pay"
            requires_confirmation = True
        else:
            action = "status"
    elif module == "healthcare":
        if "book" in prompt_lower or "confirm" in prompt_lower:
            action = "book_appointment"
            requires_confirmation = True
        else:
            action = "find_slots"
    elif module == "recruitment":
        if "apply" in prompt_lower or "submit" in prompt_lower:
            action = "apply"
            requires_confirmation = True
        else:
            action = "search"
    elif module == "student_opportunities":
        if "apply" in prompt_lower or "submit" in prompt_lower:
            action = "apply"
            requires_confirmation = True
        else:
            action = "search"

    return {
        "module": module,
        "target": prompt.strip(),
        "action": action,
        "requires_confirmation": requires_confirmation,
        "parameters": {"fallback_note": f"Rule-based classification used (API status: {error})"},
    }