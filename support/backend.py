"""A pretend support backend: three customers, four orders and the four operations the
CCAR-F Customer Support scenario names. Plain Python with no SDK, so both demos share it.

Two things are deliberately left out of these functions:

- process_refund does not check the agent refund limit. A backend executes what it is told;
  the limit is policy and lives in the harness (the hooks), where it applies to every caller.
- Nothing here checks that the customer was verified first. That ordering is a property of
  the conversation, so it is enforced around the tools, not inside them.

The two tools also disagree about formats on purpose (Unix timestamps from get_customer,
ISO 8601 and numeric status codes from lookup_order), so that the PostToolUse normaliser has
real work to do.
"""
from datetime import datetime, timedelta, timezone

NOW = datetime.now(timezone.utc).replace(microsecond=0)


def _days_ago(days):
    return NOW - timedelta(days=days)


CUSTOMERS = [
    {"customer_id": "CUST-0001", "name": "Ivan Petrov", "email": "ivan.petrov@example.com",
     "phone": "07700900001", "tier": "standard",
     "created": int(_days_ago(420).timestamp()), "last_contact_at": int(_days_ago(3).timestamp())},
    {"customer_id": "CUST-0002", "name": "Ada Whitfield", "email": "ada.whitfield@example.com",
     "phone": "07700900007", "tier": "plus",
     "created": int(_days_ago(200).timestamp()), "last_contact_at": int(_days_ago(40).timestamp())},
    {"customer_id": "CUST-0003", "name": "Sam Okafor", "email": "sam.okafor@example.com",
     "phone": "07700900012", "tier": "standard",
     "created": int(_days_ago(90).timestamp()), "last_contact_at": int(_days_ago(1).timestamp())},
]

STATUS_CODES = {10: "placed", 20: "dispatched", 30: "delivered", 40: "returned", 50: "cancelled"}


def _order(order_id, customer_id, item, sku, pence, delivered_days_ago):
    """An order record shaped like a real one: 33 fields, of which a refund needs five."""
    delivered = _days_ago(delivered_days_ago)
    return {
        "order_id": order_id, "customer_id": customer_id, "status": 30,
        "status_detail": "left with resident",
        "placed_at": (delivered - timedelta(days=3)).isoformat(),
        "dispatched_at": (delivered - timedelta(days=1)).isoformat(),
        "delivered_at": delivered.isoformat(), "updated_at": delivered.isoformat(),
        "currency": "GBP", "subtotal_pence": pence, "shipping_pence": 0, "tax_pence": 0,
        "total_pence": pence, "discount_pence": 0, "refunded_pence": 0,
        "payment_method": "card", "payment_reference": "PAY-" + order_id[-4:],
        "invoice_id": "INV-" + order_id[-4:], "shipment_id": "SHP-" + order_id[-4:],
        "carrier": "Northbound Logistics",
        "tracking_url": "https://tracking.example.com/SHP-" + order_id[-4:],
        "warehouse": "LEE-2", "channel": "web", "locale": "en-GB", "item_sku": sku,
        "item_name": item, "item_quantity": 1, "item_unit_pence": pence, "gift_wrap": False,
        "marketing_source": "organic", "weight_grams": 1450, "return_window_days": 30,
        "signature_required": pence > 50000,
    }


ORDERS = [
    _order("ORD-0021", "CUST-0001", "Barista Pro espresso machine", "SKU-902", 65000, 4),
    _order("ORD-0003", "CUST-0001", "Ridgeline walking boots", "SKU-441", 8999, 6),
    _order("ORD-0014", "CUST-0002", "Cast iron cookware set", "SKU-310", 21000, 10),
    _order("ORD-0030", "CUST-0003", "Trail running jacket", "SKU-118", 12900, 2),
]

# What actually happened, as opposed to what the model said happened.
LEDGER = {"refunds": [], "escalations": []}


def reset():
    LEDGER["refunds"].clear()
    LEDGER["escalations"].clear()


class ToolFailure(Exception):
    """A failure the agent can act on: category, whether a retry helps, what to do next."""

    def __init__(self, category, message, retryable, **extra):
        super().__init__(message)
        self.payload = {"errorCategory": category, "isRetryable": retryable,
                        "message": message, **extra}


def get_customer(identifier):
    """Verify a customer from an email address, phone number or customer id. A name is
    not an identifier: two people can share one."""
    needle = str(identifier).strip().lower()
    matches = [c for c in CUSTOMERS
               if needle in (c["customer_id"].lower(), c["email"].lower(), c["phone"])]
    if not matches:
        raise ToolFailure(
            "validation", "No account matches " + repr(str(identifier)) + ".", False,
            suggestion="Ask the customer for their email address, phone number or "
                       "customer id. A name alone cannot verify an account.")
    found = dict(matches[0])
    found["matches"] = len(matches)
    found["verified_customer_id"] = found["customer_id"] if len(matches) == 1 else None
    return found


def _check_customer_id(customer_id):
    if not str(customer_id).startswith("CUST-"):
        raise ToolFailure("validation", "customer_id must be the verified_customer_id that "
                          "get_customer returned, such as CUST-0001, not an email or name.",
                          True)


def lookup_order(order_id, customer_id):
    _check_customer_id(customer_id)
    order_id = str(order_id).strip().upper()
    for record in ORDERS:
        if record["order_id"] == order_id:
            if record["customer_id"] != customer_id:
                raise ToolFailure("permission", "Order " + order_id + " belongs to a "
                                  "different customer.", False)
            return dict(record)
    raise ToolFailure("validation", "No order " + order_id + ".", False,
                      suggestion="Ask the customer to read the order number from their email.")


def process_refund(order_id, customer_id, amount, reason):
    _check_customer_id(customer_id)
    order_id = str(order_id).strip().upper()
    record = next((r for r in ORDERS if r["order_id"] == order_id), None)
    if record is None:
        raise ToolFailure("validation", "No order " + order_id + ".", False)
    if record["customer_id"] != customer_id:
        raise ToolFailure("permission", "Order " + order_id + " belongs to a different "
                          "customer.", False)
    refund = {"refund_id": "REF-" + order_id[-4:], "order_id": order_id,
              "customer_id": customer_id, "amount_gbp": round(float(amount), 2),
              "reason": reason, "state": "processed"}
    LEDGER["refunds"].append(refund)
    return refund


HANDOFF_REQUIRED = ("customer_id", "root_cause", "refund_amount", "recommended_action")


def escalate_to_human(handoff):
    """Queue the case for a human who cannot read the conversation. The four fields the
    exam names are required; a handoff missing one is sent back."""
    missing = [f for f in HANDOFF_REQUIRED if not str(handoff.get(f) or "").strip()]
    if missing:
        raise ToolFailure("validation", "The handoff is not self-contained. Missing: "
                          + ", ".join(missing) + ".", True,
                          suggestion="Resend with every required field stated in full.")
    ticket = {"ticket": "ESC-" + str(len(LEDGER["escalations"]) + 1).zfill(4),
              "state": "queued", "handoff": dict(handoff)}
    LEDGER["escalations"].append(ticket)
    return ticket
