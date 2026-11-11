"""The support agent's hooks. Prompts ask; these run as code on every call.

Each hook is wired to its tools in run.py (the matcher), so a hook never has to
check which tool it is looking at.
"""
from datetime import datetime, timezone

from plumbing import replace_result, result_of

REFUND_LIMIT_GBP = 500

# What the harness remembers between calls. Claude cannot write here.
memory = {"verified_customer_id": None}


def reset():
    memory["verified_customer_id"] = None


def deny(reason):
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason}}


# Rule 1: the refund limit. PreToolUse on process_refund.

async def enforce_refund_limit(input_data, tool_use_id, context):
    amount = input_data["tool_input"]["amount"]
    if amount > REFUND_LIMIT_GBP:
        return deny("Refunds over £500 need a human. Call "
                    "escalate_to_human with the customer id, root "
                    "cause, amount and recommended action.")
    return {}


# Rule 2: verify first. One hook writes the memory, one reads it.

async def record_verification(input_data, tool_use_id, context):
    """PostToolUse on get_customer."""
    customer = result_of(input_data)
    if customer.get("matches") == 1:
        memory["verified_customer_id"] = customer["customer_id"]
    return {}


async def require_verification(input_data, tool_use_id, context):
    """PreToolUse on lookup_order and process_refund."""
    if memory["verified_customer_id"] is None:
        return deny("Verify the customer with get_customer first. "
                    "Ask for an email address, phone number or "
                    "customer id.")
    return {}


# Data hygiene: one shape for every result. PostToolUse on every tool.

STATUS = {10: "placed", 20: "dispatched", 30: "delivered",
          40: "returned", 50: "cancelled"}
KEEP = ("order_id", "status", "delivered_at", "total_pence", "item_name")


async def normalise_tool_output(input_data, tool_use_id, context):
    result = result_of(input_data)
    if not result or "errorCategory" in result:
        return {}
    clean = dict(result)
    for field in ("created", "last_contact_at"):          # Unix -> ISO 8601
        if isinstance(clean.get(field), int):
            clean[field] = datetime.fromtimestamp(
                clean[field], tz=timezone.utc).isoformat()
    if isinstance(clean.get("status"), int):              # 30 -> "delivered"
        clean["status"] = STATUS.get(clean["status"], clean["status"])
    if "total_pence" in clean:                            # 33 fields -> 5
        clean = {key: clean[key] for key in KEEP}
    if clean == result:
        return {}
    return replace_result(input_data, clean)
