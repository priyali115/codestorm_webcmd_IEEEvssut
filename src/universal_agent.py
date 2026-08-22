"""Interactive orchestration and CLI entry point for the Universal AI Browser Agent."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable

# Ensure project root is in sys.path for direct script execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.brain import analyze_and_route_intent
from src.memory import (
    get_billing_accounts,
    get_healthcare_preferences,
    get_recruitment_company,
    get_student_profile,
    load_memory,
)
from src.webcmd_bridge import execute_webcmd, resolve_adapter_path

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
        return {
            "student_profile": get_student_profile(),
            "recruitment_company": get_recruitment_company(),
        }
    if module == "bills":
        return {"billing_accounts": get_billing_accounts()}
    if module == "healthcare":
        return {"healthcare_preferences": get_healthcare_preferences()}
    raise ValueError(f"Unsupported module: {module}")


def build_command_preview(
    module: str,
    args: dict[str, Any],
    profile: str | None = None,
    session: str | None = None,
) -> str:
    """Construct a clean string preview of the WebCMD command to be executed."""
    adapter = ADAPTERS.get(module, module)
    try:
        adapter_file = resolve_adapter_path(adapter)
    except FileNotFoundError:
        adapter_file = f"adapters/{adapter}.js"

    cmd_parts = ["webcmd", "browser", "run", "--file", f'"{adapter_file}"', "-f", "json"]
    if profile:
        cmd_parts.extend(["--profile", profile])
    if session:
        cmd_parts.extend(["--session", session])

    for key, value in args.items():
        if value is None or value is False:
            continue
        flag = str(key).replace("_", "-")
        if value is True:
            cmd_parts.append(f"--{flag}")
        else:
            if isinstance(value, (dict, list)):
                cmd_parts.append(f'--{flag} \'{json.dumps(value)}\'')
            else:
                cmd_parts.append(f'--{flag} "{value}"')

    return " ".join(cmd_parts)


def run_agent_pipeline(
    user_prompt: str,
    override_action: str | None = None,
    profile: str | None = None,
    session: str | None = None,
) -> dict[str, Any]:
    """Execute the full AI Agent pipeline: Brain routing -> Context injection -> WebCMD Bridge."""
    intent = analyze_and_route_intent(user_prompt)
    if override_action:
        intent["action"] = override_action

    module = intent["module"]
    context = _context_for(module)

    # Prepare adapter arguments
    args = {
        "target": intent.get("target", ""),
        "action": intent.get("action", "search"),
        **intent.get("parameters", {}),
        **context,
    }

    command_str = build_command_preview(module, args, profile, session)
    adapter_name = ADAPTERS[module]

    # Execute via WebCMD Bridge
    result = execute_webcmd(
        adapter_name=adapter_name,
        args_dict=args,
        profile=profile,
        session=session,
    )

    return {
        "intent": intent,
        "context": context,
        "args": args,
        "command_str": command_str,
        "result": result,
    }


def handle_prompt(
    user_prompt: str,
    input_fn: Callable[[str], str] = input,
    profile: str | None = None,
    session: str | None = None,
) -> dict[str, Any]:
    """Interactive handler with confirmation for high-impact actions."""
    intent = analyze_and_route_intent(user_prompt)
    module = intent["module"]
    context = _context_for(module)
    requires_confirmation = intent.get("requires_confirmation", False)

    args = {
        "target": intent.get("target", ""),
        "action": intent.get("action", "search"),
        **intent.get("parameters", {}),
        **context,
    }

    adapter_name = ADAPTERS[module]

    if requires_confirmation:
        # Generate dry-run preview if action is high impact
        preview_args = {**args, "action": "status" if module == "bills" else "find_slots"}
        preview = execute_webcmd(adapter_name, preview_args, profile=profile, session=session)
        
        print("\n=== HIGH IMPACT ACTION CONFIRMATION REQUIRED ===")
        print(f"Module: {module}")
        print(f"Action: {intent.get('action')}")
        print(f"Target: {intent.get('target')}")
        print("Dry-run preview result:")
        print(json.dumps(preview, indent=2, ensure_ascii=False))
        print("=================================================\n")

        answer = input_fn(f"Confirm execution of action '{intent.get('action')}'? (type 'yes' to proceed): ").strip().lower()
        if answer != "yes":
            return {
                "intent": intent,
                "context": context,
                "command_str": build_command_preview(module, args, profile, session),
                "result": {"status": "cancelled", "message": "User declined action confirmation."},
            }

    command_str = build_command_preview(module, args, profile, session)
    result = execute_webcmd(adapter_name, args, profile=profile, session=session)

    return {
        "intent": intent,
        "context": context,
        "command_str": command_str,
        "result": result,
    }


def main() -> None:
    print("=" * 60)
    print("🤖 Universal AI Browser Agent - CLI Orchestrator")
    print("Type 'exit' or 'quit' to stop.")
    print("=" * 60)
    
    while True:
        try:
            prompt = input("\nUser Prompt > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return
        if prompt.lower() in {"exit", "quit"}:
            print("Goodbye!")
            return
        if not prompt:
            continue
        try:
            output = handle_prompt(prompt)
            print("\n--- AGENT RESPONSE ---")
            print(json.dumps(output, indent=2, ensure_ascii=False))
        except Exception as exc:
            print(f"\n[ERROR] Agent failed: {exc}")


if __name__ == "__main__":
    main()
