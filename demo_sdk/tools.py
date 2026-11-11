"""The four support tools, served in-process by the Agent SDK as an MCP server named
"support". That key is why the agent sees them as mcp__support__get_customer and so on."""
import json
import sys
from pathlib import Path

from claude_agent_sdk import create_sdk_mcp_server, tool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from support import backend  # noqa: E402


def ok(payload):
    return {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]}


def failed(exc):
    # is_error is the SDK's spelling; on the MCP wire it travels as isError.
    return {"content": [{"type": "text", "text": json.dumps(exc.payload, indent=2)}],
            "is_error": True}


async def _call(fn, *args):
    try:
        return ok(fn(*args))
    except backend.ToolFailure as exc:
        return failed(exc)


@tool("get_customer",
      "Verify who you are talking to from an email address, phone number or customer id. "
      "Returns verified_customer_id only when exactly one account matches. A name alone "
      "is not accepted.",
      {"identifier": str})
async def get_customer(args):
    return await _call(backend.get_customer, args["identifier"])


CUSTOMER_ID = {"type": "string",
               "description": "The verified_customer_id from get_customer, such as CUST-0001."}


@tool("lookup_order",
      "Fetch the order record for one order id: status, dates, amount and item. Needs the "
      "verified customer id.",
      {"type": "object",
       "properties": {"order_id": {"type": "string", "description": "Such as ORD-0021."},
                      "customer_id": CUSTOMER_ID},
       "required": ["order_id", "customer_id"]})
async def lookup_order(args):
    return await _call(backend.lookup_order, args["order_id"], args["customer_id"])


@tool("process_refund",
      "Refund an amount in pounds against an order, with a reason. Needs the verified "
      "customer id.",
      {"type": "object",
       "properties": {"order_id": {"type": "string"}, "customer_id": CUSTOMER_ID,
                      "amount": {"type": "number", "description": "In pounds, such as 89.99."},
                      "reason": {"type": "string"}},
       "required": ["order_id", "customer_id", "amount", "reason"]})
async def process_refund(args):
    return await _call(backend.process_refund, args["order_id"], args["customer_id"],
                       args["amount"], args["reason"])


@tool("escalate_to_human",
      "Hand the case to a human agent who cannot see this conversation. The handoff must "
      "stand on its own: who the customer is, what went wrong, the amount at stake and what "
      "you recommend.",
      {"type": "object",
       "properties": {
           "customer_id": CUSTOMER_ID,
           "root_cause": {"type": "string", "description": "What went wrong, in one or two sentences."},
           "refund_amount": {"type": "string", "description": "The amount at stake, in pounds."},
           "recommended_action": {"type": "string", "description": "What the human should do."},
           "order_id": {"type": "string"},
           "actions_taken": {"type": "array", "items": {"type": "string"}},
       },
       "required": ["customer_id", "root_cause", "refund_amount", "recommended_action"]})
async def escalate_to_human(args):
    return await _call(backend.escalate_to_human, args)


TOOLS = [get_customer, lookup_order, process_refund, escalate_to_human]
TOOL_NAMES = ["mcp__support__" + t.name for t in TOOLS]
server = create_sdk_mcp_server(name="support", version="1.0.0", tools=TOOLS)
