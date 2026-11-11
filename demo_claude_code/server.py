"""The same four support tools as the SDK demo, served over stdio as an MCP server so
Claude Code can use them. Claude Code starts it from .mcp.json.

Every refund and escalation is appended to ledger.jsonl next to this file, so you can see
what actually happened in the backend, whatever the agent says happened.
"""
import json
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from support import backend  # noqa: E402

LEDGER = HERE / "ledger.jsonl"
mcp = FastMCP("support")


def _call(fn, *args):
    try:
        return fn(*args)
    except backend.ToolFailure as exc:
        # FastMCP turns a raised exception into a result with isError: true.
        raise RuntimeError(json.dumps(exc.payload)) from None


def _record(kind, entry):
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": kind, **entry}) + "\n")


@mcp.tool()
def get_customer(identifier: str) -> dict:
    """Verify who you are talking to from an email address, phone number or customer id.
    Returns verified_customer_id only when exactly one account matches. A name alone is not
    accepted."""
    return _call(backend.get_customer, identifier)


@mcp.tool()
def lookup_order(order_id: str, customer_id: str) -> dict:
    """Fetch the order record for one order id: status, dates, amount and item. Needs the
    verified customer id."""
    return _call(backend.lookup_order, order_id, customer_id)


@mcp.tool()
def process_refund(order_id: str, customer_id: str, amount: float, reason: str) -> dict:
    """Refund an amount in pounds against an order, with a reason. Needs the verified
    customer id."""
    refund = _call(backend.process_refund, order_id, customer_id, amount, reason)
    _record("refund", refund)
    return refund


@mcp.tool()
def escalate_to_human(customer_id: str, root_cause: str, refund_amount: str,
                      recommended_action: str, order_id: str = "",
                      actions_taken: list[str] | None = None) -> dict:
    """Hand the case to a human agent who cannot see this conversation. The handoff must
    stand on its own: who the customer is, what went wrong, the amount at stake and what
    you recommend."""
    handoff = {"customer_id": customer_id, "root_cause": root_cause,
               "refund_amount": refund_amount, "recommended_action": recommended_action,
               "order_id": order_id, "actions_taken": actions_taken or []}
    ticket = _call(backend.escalate_to_human, handoff)
    _record("escalation", ticket)
    return ticket


if __name__ == "__main__":
    mcp.run()
