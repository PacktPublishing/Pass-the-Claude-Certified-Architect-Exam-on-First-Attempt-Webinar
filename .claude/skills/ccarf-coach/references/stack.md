# The Claude stack in exam terms

Each section: what it is, what the exam tests, the decision rule, the classic distractor,
where this kit shows it, and the official links. Where the current product differs from
the exam guide, the exam's answer comes first and the change follows in one sentence.

## How the four fit together

The **Claude API** is one stateless call: messages in, content blocks out. The **agentic
loop** sits on top of it: Claude decides, your code runs the tool, the result goes back,
until Claude ends the turn. There are three ways to get that loop: write it yourself against
the API, use the **Agent SDK** in your own program, or use **Claude Code** in a terminal.
**MCP** is not a fourth engine: it is how tools reach whichever of the three you picked.

---

## 1. The Claude API

**What it is.** The Messages API. It keeps no state: your code sends the whole conversation,
including every `tool_use` and `tool_result`, on every call.

**What the exam tests.**
- The tool-use loop: continue while `stop_reason` is `"tool_use"`, stop on `"end_turn"`, and
  return each `tool_result` with the matching `tool_use_id`.
- `tool_choice`: `"auto"` (Claude may answer in text), `"any"` (Claude must call a tool, its
  choice), or a forced named tool. Forcing a tool makes a call happen; it does not make the
  right call or enforce a policy.
- Structured output: tool use with a JSON schema is the exam's "most reliable" answer.
  Unknown document type with several schemas: `"any"`. A step that must run first: force it.
- Schema design: nullable fields when a value may be absent (otherwise the model invents
  one), `enum` with `"other"` plus a detail field, an `"unclear"` value. A schema-valid answer
  can still be wrong (totals that do not add up): validate in code and retry with the errors.
- Message Batches: 50% of the cost, results within 24 hours with no latency guarantee,
  `custom_id` to match results, and no multi-turn tool use inside one request.

**Decision rule.** Need the structure guaranteed: a schema, not a sentence asking for JSON.
Need it cheap and not urgent: batches. Need it now or interactive: the synchronous API.

**Classic distractor.** "Respond only with valid JSON" in the prompt; or retrying an
extraction that failed because the information is not in the document.

**Current product.** Native structured outputs (`output_config.format`, or
`client.messages.parse()` with a Pydantic model) constrain the reply itself and are what
code that only needs the record back uses today; the exam's answer stays tool use with a
JSON schema.

**Links.**
https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
https://platform.claude.com/docs/en/build-with-claude/structured-outputs
https://platform.claude.com/docs/en/build-with-claude/batch-processing

---

## 2. MCP (Model Context Protocol)

**What it is.** A protocol that lets one server expose tools, resources and prompts to any
host (Claude Code, the Agent SDK, other clients). Write the integration once, reuse it
everywhere. Every configured server's tools are available at once.

**What the exam tests.**
- Tools (Claude calls them), resources (content the application exposes, such as a catalogue
  that saves exploratory tool calls) and prompts (templates the user picks).
- Tool descriptions are how Claude selects a tool. Minimal or overlapping descriptions cause
  misrouting: expand them first (inputs, examples, edge cases, when to use which), rename to
  remove overlap, or split a generic tool into purpose-specific ones. A keyword in the system
  prompt can override a good description.
- Structured errors: `isError: true`, an error category (transient, validation, business,
  permission), whether a retry can help, and a readable message. A generic "Operation failed"
  blocks recovery. An empty result means "searched, found nothing"; never return it for a
  timeout. Retry transient failures inside the tool, then report what is left.
- Configuration: project servers in `.mcp.json` (shared through version control), personal
  servers in `~/.claude.json`, secrets through environment variables. Tool names appear as
  `mcp__<server>__<tool>`.

**Decision rule.** Misrouting with thin descriptions: fix the descriptions. Misrouting with
good descriptions that tracks a keyword: fix the system prompt. Failures the agent cannot act
on: return structured error metadata.

**Classic distractor.** Few-shot examples or a keyword routing layer to fix tool selection;
reporting a failure as an empty success.

**In this kit.** `support/backend.py` and `demo_sdk/tools.py`: tools return
`errorCategory` and `isRetryable` on failure; `demo_claude_code/server.py` serves the same
tools over stdio.

**Links.**
https://modelcontextprotocol.io/introduction
https://modelcontextprotocol.io/docs/learn/architecture
https://code.claude.com/docs/en/mcp

---

## 3. The Claude Agent SDK

**What it is.** The agentic loop as a library: the same tools, loop and context management
that power Claude Code, inside your own Python or TypeScript program.

**What the exam tests.**
- `ClaudeAgentOptions` defines the agent (system prompt, tools, MCP servers, hooks, limits);
  `query()` runs one task; `ClaudeSDKClient` keeps a conversation going.
- Custom tools: `@tool` (name, description, input schema, handler) served by an in-process
  MCP server from `create_sdk_mcp_server`, passed in `mcp_servers`.
- `allowed_tools` approves tools so they run without a permission prompt; it does not take
  other tools away. Restriction is `tools` (what exists) and `disallowed_tools`. Give each
  agent only the tools its role needs: a few tools select better than many.
- Hooks: `PreToolUse` runs before a call and can deny or rewrite it; `PostToolUse` runs after
  and can rewrite the result before Claude reads it. A hook's deny holds whatever the prompt
  says. A denial's reason goes back to Claude as the tool result, so name the next step in it.
- Subagents: `AgentDefinition` (description, prompt, tools, model) and the `Task` tool, which
  the coordinator's `allowedTools` must include. Subagents do not inherit the coordinator's
  conversation: pass complete findings in the prompt, with sources. Spawn parallel subagents
  in one response.
- Sessions: resume a session by id or name, fork from a shared baseline, or start fresh with a
  structured summary when old tool results are stale.
- Loop control: `stop_reason` ends the loop; an iteration cap is a safety net, not the
  stopping rule.

**Decision rule.** A rule with a financial, legal or safety cost if broken: a hook, not a
prompt. A rule that is a preference or has legitimate exceptions: the prompt.

**Classic distractor.** A stronger system prompt, more few-shot examples or "ask the model to
double-check" for something that must hold every time; `allowed_tools` as a restriction; a
subagent that "remembers" the coordinator's context.

**Current product.** The `Task` tool is named `Agent` in current Claude Code releases, and
`Task` is still accepted; the exam says `Task`.

**In this kit.** `steps/01_simple_agent.py`, `steps/02_add_a_tool.py`,
`steps/03_add_a_hook.py`, then `demo_sdk/hooks.py` (refund limit, record-and-block identity
gate, `PostToolUse` normaliser) wired in `demo_sdk/run.py`.

**Links.**
https://code.claude.com/docs/en/agent-sdk/overview
https://code.claude.com/docs/en/agent-sdk/custom-tools
https://code.claude.com/docs/en/agent-sdk/hooks
https://code.claude.com/docs/en/agent-sdk/subagents
https://code.claude.com/docs/en/agent-sdk/sessions
https://code.claude.com/docs/en/agent-sdk/structured-outputs

---

## 4. Claude Code

**What it is.** The agentic loop in a terminal, configured by files in your repository.

**What the exam tests.**
- CLAUDE.md levels: user (`~/.claude/CLAUDE.md`, yours only), project (shared through version
  control) and directory (a subfolder's file). They add up rather than override. A teammate
  missing an instruction usually means it lives at user level. `/memory` shows what loaded.
- Modular configuration: `@path` imports (loaded in full at session start) and
  `.claude/rules/` files. A rule file with `paths:` globs in its frontmatter loads only when
  Claude works on matching files, which beats copies of a subdirectory CLAUDE.md for a
  convention that follows a file type across folders.
- Slash commands and skills: `.claude/commands/` for the team, `~/.claude/commands/` for
  you; `SKILL.md` frontmatter. Which surface owns which rule: CLAUDE.md for always-on
  standards, a skill for a procedure used sometimes, a hook for what must always hold.
- Plan mode for large, multi-file changes with several valid approaches; direct execution for
  a clear, well-scoped change; the Explore subagent to keep verbose discovery out of the main
  context.
- Headless and CI: `-p` for non-interactive runs, `--output-format json` with `--json-schema`,
  and read `structured_output` instead of trusting the exit code. On a rerun of a review, pass
  the earlier findings in and report only new or unresolved issues. An independent reviewer
  finds more than the session that wrote the code.

**Decision rule.** Always true for everyone on the team: project CLAUDE.md or a rule file.
Only for some files: a `paths:` rule. A procedure: a skill or command. Must never be broken:
a hook.

**Classic distractor.** "Switch to plan mode if it gets complicated" when the scenario already
describes the complexity; an `@` import to "save context"; a subdirectory CLAUDE.md in every
folder.

**Current product.** Commands and skills have been unified (both create `/name`) and
`.claude/commands/` still works; the exam says `.claude/commands/`.

**In this kit.** `demo_claude_code/.claude/settings.json` (hooks) and
`demo_claude_code/CLAUDE.md`; this skill itself is a `SKILL.md` in `.claude/skills/`.

**Links.**
https://code.claude.com/docs/en/memory
https://code.claude.com/docs/en/skills
https://code.claude.com/docs/en/hooks
https://code.claude.com/docs/en/common-workflows
https://code.claude.com/docs/en/headless
https://code.claude.com/docs/en/github-actions

---

## 5. Across the stack

**Enforcement and handoff.** Prompts ask, hooks enforce. When an agent hands a case to a
human who has no transcript, the handoff carries at least the customer ID, the root cause,
the amount and the recommended action, as fields rather than prose.

**Prompting.** Explicit, checkable criteria beat "be conservative". Reduce false positives by
anchoring each severity level to an example and disabling a noisy category while you fix it.
Use a few examples chosen for the boundary cases, not many generic ones.

**Context and reliability.**
- Keep a case-facts block (ids, amounts, dates) outside the summarised history; put key
  findings first; trim tool output; direct compaction instead of running it bare.
- Escalate on an explicit request, a gap in policy, or no progress; not on sentiment or a
  self-rated confidence score. Several matching customers: ask for another identifier.
- Across agents: recover locally, then report what failed, what was tried and any partial
  results; never hide a failure as an empty success.
- Human review: an aggregate accuracy can hide a failing document type; validate by type and
  field, sample high-confidence results, and calibrate confidence before routing on it.
- Provenance: keep each claim with its source; show established, contested and missing
  findings; render each content type in its natural format.

**Link.** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
