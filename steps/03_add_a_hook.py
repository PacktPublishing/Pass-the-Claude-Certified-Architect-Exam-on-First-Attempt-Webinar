"""Step 3: add hooks. PreToolUse runs before the tool, PostToolUse after it,
before Claude reads the result. Here they only print; returning {} means
"no objection", so the call goes ahead.

    uv run steps/03_add_a_hook.py
"""
import asyncio

from claude_agent_sdk import (ClaudeAgentOptions, HookMatcher, ResultMessage,
                              create_sdk_mcp_server, query, tool)

CUSTOMERS = {"ivan.petrov@example.com": "CUST-0001, Ivan Petrov"}


@tool("get_customer", "Look up a customer by email address.",
      {"email": str})
async def get_customer(args):
    customer = CUSTOMERS.get(args["email"], "No such customer.")
    return {"content": [{"type": "text", "text": customer}]}


async def before_call(input_data, tool_use_id, context):
    print("PreToolUse: Claude wants", input_data["tool_input"])
    return {}


async def after_call(input_data, tool_use_id, context):
    result = input_data["tool_response"]
    print("PostToolUse: the tool returned", result)
    return {}


server = create_sdk_mcp_server("support", tools=[get_customer])

options = ClaudeAgentOptions(
    system_prompt="You are a support agent for an online shop.",
    mcp_servers={"support": server},
    allowed_tools=["mcp__support__get_customer"],
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="mcp__support__get_customer",
                        hooks=[before_call])],
        "PostToolUse": [
            HookMatcher(matcher="mcp__support__get_customer",
                        hooks=[after_call])],
    },
)


async def main():
    task = "I'm ivan.petrov@example.com. What's my customer id?"
    async for message in query(prompt=task, options=options):
        if isinstance(message, ResultMessage):
            print(message.result)


asyncio.run(main())
