#!/usr/bin/env python3
"""The SDK demo's gates as Claude Code command hooks. Standard library only.

Claude Code runs this with the hook event as JSON on stdin and reads a JSON decision from
stdout. One script, three jobs, chosen by the first argument:

    gate.py record   PostToolUse on get_customer: remember a verified id for this session
    gate.py verify   PreToolUse on lookup_order and process_refund: deny until verified
    gate.py limit    PreToolUse on process_refund: deny over £500, redirect to a human

A command hook is a separate process each time, so the verified id is kept in a small file
per session rather than in memory.
"""
import json
import sys
from pathlib import Path

REFUND_LIMIT_GBP = 500.00
STATE_DIR = Path(__file__).resolve().parent / ".state"


def deny(reason):          # printed to stdout as JSON, exit code 0
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason}}))


def state_file(event):
    return STATE_DIR / (str(event.get("session_id") or "default") + ".json")


def payload_of(response):
    """Find the JSON a tool returned, whether Claude Code hands over a dict, a list of
    content blocks, a {"content": [...]} wrapper or a string."""
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except ValueError:
            return None
    if isinstance(response, dict) and isinstance(response.get("structuredContent"), dict):
        return payload_of(response["structuredContent"])
    if isinstance(response, dict) and isinstance(response.get("content"), list):
        response = response["content"]
    if isinstance(response, list):
        for block in response:
            if isinstance(block, dict) and block.get("type") == "text":
                return payload_of(block.get("text"))
        return None
    return response if isinstance(response, dict) else None


def record(event):
    payload = payload_of(event.get("tool_response"))
    if payload and payload.get("matches") == 1 and payload.get("verified_customer_id"):
        STATE_DIR.mkdir(exist_ok=True)
        state_file(event).write_text(json.dumps(
            {"verified_customer_id": payload["verified_customer_id"]}))


def verify(event):
    path = state_file(event)            # one file per session
    verified = (json.loads(path.read_text()).get("verified_customer_id")
                if path.exists() else None)
    if not verified:
        deny("Verify the customer with get_customer before any order "
             "or refund operation. Ask for an email address, phone "
             "number or customer id.")


def limit(event):
    amount = float((event.get("tool_input") or {}).get("amount") or 0)
    if amount > REFUND_LIMIT_GBP:
        deny(f"A refund of \u00a3{amount:.2f} is over the \u00a3500 agent "
             "limit and needs a human. Call escalate_to_human with the "
             "customer id, the root cause, the amount and a recommended "
             "action.")


if __name__ == "__main__":
    {"record": record, "verify": verify, "limit": limit}[sys.argv[1]](json.load(sys.stdin))
