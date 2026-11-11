"""Plumbing the hooks need but the slides do not show.

An MCP tool answers with typed content blocks, so the JSON a rule needs sits
inside a text block. These helpers read it out and put a rewritten version back.
"""
import json


def result_of(input_data):
    """The JSON a tool returned, as a dict ({} if there is none)."""
    response = input_data.get("tool_response")
    if isinstance(response, dict) and isinstance(response.get("content"), list):
        response = response["content"]
    if isinstance(response, list):
        for block in response:
            if isinstance(block, dict) and block.get("type") == "text":
                try:
                    parsed = json.loads(block["text"])
                except (ValueError, TypeError):
                    return {}
                return parsed if isinstance(parsed, dict) else {}
        return {}
    return response if isinstance(response, dict) else {}


def replace_result(input_data, new_result):
    """A PostToolUse answer that swaps what Claude reads for new_result."""
    block = {"type": "text", "text": json.dumps(new_result, indent=2)}
    response = input_data.get("tool_response")
    if isinstance(response, dict) and isinstance(response.get("content"), list):
        rewritten = {**response, "content": [block]}
    elif isinstance(response, list):
        rewritten = [block]
    else:
        rewritten = new_result
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                   "updatedToolOutput": rewritten}}
