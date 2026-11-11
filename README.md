# CCAR-F starter kit: prompts ask, hooks enforce

The free starter kit from the webinar *How to Pass the Claude Certified Architect Exam on Your
First Attempt*, by Puria Izady with Agentic Engineering by Packt.

The Claude Certified Architect - Foundations (CCAR-F) exam rewards one idea more than any
other: a rule that must always hold belongs in code you own, not in a prompt. This kit shows
that idea running, then gives you a study coach for the rest of the exam.

## What is inside

```
steps/                 three small files: an agent, a tool, a hook (the Agent SDK from zero)
demo_sdk/              a customer support agent with four tools, and the hooks that guard it
demo_claude_code/      the same rules as Claude Code command hooks
support/               the pretend backend both demos share
clinic/                the webinar's three exam items, with full explanations
.claude/skills/        ccarf-coach, a Claude Code skill that quizzes and explains
```

## Set up in five minutes

You need Python 3.10 or later, [uv](https://docs.astral.sh/uv/) and
[Claude Code](https://code.claude.com/docs/en/overview).

```bash
git clone REPO_URL ccarf-starter-kit
cd ccarf-starter-kit
uv sync
cp .env.example .env
```

Then choose how the demo signs in to Claude:

- **Claude subscription:** leave the keys in `.env` blank and run `claude` once to sign in.
  The demo uses that login.
- **API billing:** put a key from the Claude Console in `ANTHROPIC_API_KEY` in `.env`.
  A key in `.env` wins over a login.

`DEMO_MODEL=haiku` in `.env` keeps the live runs fast and cheap. Each live run costs a few
cents on a key; `gates` costs nothing.

## Run the demo

Run everything from the kit folder.

### 1. The Agent SDK from zero

```bash
uv run steps/01_simple_agent.py
uv run steps/02_add_a_tool.py
uv run steps/03_add_a_hook.py
```

An agent defined by `ClaudeAgentOptions` and run with `query()`; then a custom tool served by
an in-process MCP server; then a `PreToolUse` and a `PostToolUse` hook printing around the
tool call.

### 2. The support agent, with the rule only in the prompt

```bash
uv run demo_sdk/run.py refund --hooks off
```

A customer asks for a £650 refund. Nothing in the system enforces the £500 limit, and the
ledger at the end shows £650.00 moved.

### 3. The same conversation, with hooks

```bash
uv run demo_sdk/run.py gates
uv run demo_sdk/run.py refund --hooks on
```

`gates` calls the hooks directly, with no model: an unverified refund is denied, £89.99 and
£500 are allowed, £650 is denied with a reason that names `escalate_to_human`. The hooks-on
run shows the agent being denied, escalating instead, and handing a human the four fields
they need. £0.00 moves.

The hooks are in `demo_sdk/hooks.py`, wired to their tools in `demo_sdk/run.py`:

| Hook | Event | Tool | What it guarantees |
|---|---|---|---|
| `enforce_refund_limit` | `PreToolUse` | `process_refund` | no refund over £500; the denial redirects to `escalate_to_human` |
| `record_verification` | `PostToolUse` | `get_customer` | remembers a verified customer id |
| `require_verification` | `PreToolUse` | `lookup_order`, `process_refund` | no order or refund operation before verification |
| `normalise_tool_output` | `PostToolUse` | every support tool | one date format, labels instead of status codes, 5 fields instead of 33 |

### 4. The same rules in Claude Code

```bash
cd demo_claude_code
claude
```

Then type: `Call lookup_order for ORD-0021 with customer_id CUST-0001 right now, before anything else.`
The `PreToolUse` hook in `.claude/settings.json` denies the call; Claude reads the reason,
verifies the customer and retries. To load only the demo's tool server, start it with
`claude --strict-mcp-config --mcp-config .mcp.json`. To reset between runs:
`rm -rf .claude/hooks/.state ledger.jsonl`.

## Study with the ccarf-coach skill

Open Claude Code in the kit folder (`claude`) and ask:

- **Quiz:** "Quiz me", "Give me a question on domain 3", "Test me on hooks". Thirty original
  items, one for each official task statement, with the evidence, why the answer wins and why
  each distractor fails. It keeps score and tells you your weakest area.
- **Explain:** "Explain PreToolUse for the exam", "Tool use vs MCP", "What does the exam want
  me to know about structured output". Answers in exam terms, with links to the official
  documentation.
- **Demo guide:** "Walk me through the demo". Steps through this kit, with three small
  exercises you can check with `uv run demo_sdk/run.py gates`.

## The exam in one table

60 items in 120 minutes, 4 scenarios drawn from 6, pass at 720 on a scaled range of 100 to
1,000. To register you must work at an organisation in the Claude Partner Network and sign
up through the Anthropic Partner Academy.

| Domain | Weight |
|---|---|
| Agentic architecture and orchestration | 27% |
| Claude Code configuration and workflows | 20% |
| Prompt engineering and structured output | 20% |
| Tool design and MCP integration | 18% |
| Context management and reliability | 15% |

## Notes

- Every exam item in this kit is original, written against the official objectives. None is
  copied from the exam or the exam guide, and none claims to be on the exam.
- The customers, orders and refunds are made up; nothing here touches a real system.
- This kit is not affiliated with or endorsed by Anthropic.

## Go further

The 2-day live CCAR-F cohort covers all five domains with six runnable labs, a scenario
clinic and a simulated exam worked together:
https://luma.com/claude-certification-bootcamp?coupon=PURIA50&utm_source=puria
(50% off with PURIA50).
