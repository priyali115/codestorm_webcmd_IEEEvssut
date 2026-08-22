"""Interactive orchestration for the four Universal AI Browser Agent modules."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.brain import analyze_and_route_intent
from src.memory import (
    get_billing_accounts,
    get_healthcare_preferences,
    get_student_profile,
    load_memory,
)
from src.webcmd_bridge import execute_webcmd

ADAPTERS = {

    "student_opportunities": "student_portal_adapter",
    "recruitment": "recruitment_adapter",
    "bills": "billing_aggregator_adapter",
    "healthcare": "clinic_booking_adapter",
}


def _context_for(module: str) -> dict[str, Any]:
    if module == "student_opportunities":
        return {"student_profile": get_student_profile()}
    if module == "recruitment":
        memory = load_memory()
        return {
            "student_profile": get_student_profile(),
            "recruitment_company": memory.get("recruitment_company", {}),
        }
    if module == "bills":
        return {"billing_accounts": get_billing_accounts()}
    if module == "healthcare":
        return {"healthcare_preferences": get_healthcare_preferences()}
    raise ValueError(f"Unsupported module: {module}")


def _run_module(intent: dict[str, Any], input_fn: Callable[[str], str] = input) -> Any:
    module = intent["module"]
    args = {
        "target": intent.get("target", ""),
        "search_terms": ",".join(intent.get("search_terms", [])),
        **intent.get("parameters", {}),
        **_context_for(module),
    }
    if module == "bills" and intent.get("requires_confirmation"):
        preview = execute_webcmd(ADAPTERS[module], {**args, "action": "status"})
        print(json.dumps(preview, indent=2, ensure_ascii=False))
        answer = input_fn("Confirm payment execution? Type 'yes' to continue: ").strip().lower()
        if answer != "yes":
            return {"status": "cancelled", "message": "Payment was not executed."}
        args["action"] = "pay"
    return execute_webcmd(ADAPTERS[module], args)


def handle_prompt(user_prompt: str, input_fn: Callable[[str], str] = input) -> Any:
    intent = analyze_and_route_intent(user_prompt)
    result = _run_module(intent, input_fn=input_fn)
    return {"intent": intent, "result": result}


def main() -> None:
    print("Universal AI Browser Agent. Type 'exit' to quit.")
    while True:
        try:
            prompt = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return
        if prompt.lower() in {"exit", "quit"}:
            print("Goodbye.")
            return
        if not prompt:
            continue
        try:
            print(json.dumps(handle_prompt(prompt), indent=2, ensure_ascii=False))
        except Exception as exc:
            print(f"Agent error: {exc}")


if __name__ == "__main__":
    main()
