"""Step 2: give the agent a tool. @tool defines it, an in-process MCP server
serves it, and the options hand the server to the agent.

    uv run steps/02_add_a_tool.py
"""
import asyncio

from claude_agent_sdk import (ClaudeAgentOptions, ResultMessage,
                              create_sdk_mcp_server, query, tool)

CUSTOMERS = {"ivan.petrov@example.com": "CUST-0001, Ivan Petrov"}


@tool("get_customer", "Look up a customer by email address.",
      {"email": str})
async def get_customer(args):
    customer = CUSTOMERS.get(args["email"], "No such customer.")
    return {"content": [{"type": "text", "text": customer}]}


server = create_sdk_mcp_server("support", tools=[get_customer])

options = ClaudeAgentOptions(
    system_prompt="You are a support agent for an online shop.",
    mcp_servers={"support": server},
    allowed_tools=["mcp__support__get_customer"],
)


async def main():
    task = "I'm ivan.petrov@example.com. What's my customer id?"
    async for message in query(prompt=task, options=options):
        if isinstance(message, ResultMessage):
            print(message.result)


asyncio.run(main())
