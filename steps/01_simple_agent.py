"""Step 1: the simplest agent. ClaudeAgentOptions defines it, query() runs it.

    uv run steps/01_simple_agent.py
"""
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

options = ClaudeAgentOptions(
    system_prompt="You are a support agent for an online shop.",
    max_turns=1,
)


async def main():
    task = "Hi! What can you help me with?"
    async for message in query(prompt=task, options=options):
        if isinstance(message, ResultMessage):
            print(message.result)


asyncio.run(main())
