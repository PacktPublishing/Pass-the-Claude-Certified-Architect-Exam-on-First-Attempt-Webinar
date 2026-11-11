# Live exam clinic: three items

Three original exam-style items written against the official CCAR-F objectives. None is
copied from the official exam guide or its sample questions. Each comes with the evidence in
the stem, why the right answer wins, and why each other option is attractive and still wrong.

Amounts are in dollars because the exam writes them that way. The demo uses pounds.

---

## Item 1: Customer Support Resolution Agent

*Domain 1, Agentic Architecture and Orchestration. Tasks 1.4 and 1.5.*

You are building a customer support resolution agent with the Claude Agent SDK. Company
policy allows the agent to refund up to $500; anything larger needs a human's approval. The
system prompt states this limit. An audit finds that in a small share of conversations, the
agent processed refunds above $500 after customers pushed back. Refunds above $500 must never
execute, and the customer should still get a resolution path in the same conversation.

What should you do?

- **A.** Add a `PostToolUse` hook on `process_refund` that checks the amount and flags any
  refund above $500 for human review after it completes.
- **B.** Move the limit to the top of the system prompt in capitals and add three few-shot
  examples in which the agent escalates a large refund instead of processing it.
- **C.** Add a `PreToolUse` hook on `process_refund` that denies amounts above $500, with a
  reason telling the agent to call `escalate_to_human` with the customer ID, root cause,
  amount and recommended action.
- **D.** Add a `PreToolUse` hook on `process_refund` that denies amounts above $500 and
  returns the reason "Permission denied".

**Answer: C**

**Evidence in the stem.**
- "must **never** execute": a guarantee about a call, so it needs code, and it must run
  *before* the call.
- "still get a resolution path **in the same conversation**": the block has to lead somewhere.
- "the system prompt states this limit" and it still failed: the prompt has already been tried.

**Why C wins.** `PreToolUse` runs before the tool executes and the hook is code, so the
refund cannot go through on any run. The `permissionDecisionReason` comes back to the agent
as the tool result. Because it names `escalate_to_human` and the fields to hand over, the
agent's next move is the escalation. The objective pairs the two on purpose: block the
policy-violating action *and* redirect it to an alternative workflow.

**Why the others are attractive, and still wrong.**
- **A** is a hook, so it looks deterministic. But `PostToolUse` fires after the tool has run:
  the money has already gone out. It can transform a result; it cannot un-run a call.
  Prevention comes before the call, transformation after.
- **B** is what a careful engineer tries first, and it will lower the rate. It is still
  probabilistic, which the audit has already shown. A stronger prompt and more examples move
  the number, never to zero.
- **D** is the closest distractor: right hook, right timing, the refund is blocked. It fails
  the second requirement. A bare "Permission denied" leaves the agent guessing, so the
  conversation dead-ends or the agent retries with a different amount. Naming the
  alternative in the reason is what turns a refusal into a redirect.

**The question to ask of every option:** what happens on the run where the model does not
comply?

---

## Item 2: Multi-Agent Research System

*Domain 2, Tool Design and MCP Integration. Task 2.1.*

In your multi-agent research system, the document-analysis subagent has two tools,
`extract_data_points` and `verify_claim_against_source`. Each has a detailed description that
states its inputs, gives example queries and says when to use it instead of the other. Logs
show that requests like "check whether the revenue figure in this report matches the annual
filing" are routed to `extract_data_points`. Almost every misrouted request contains the word
"check", and requests without it route correctly. The subagent's system prompt includes:
"Always check documents thoroughly by extracting every data point before answering."

What is the most effective fix?

- **A.** Add five few-shot examples to the system prompt showing "check" requests routed to
  `verify_claim_against_source`.
- **B.** Add a routing step before the subagent that sends any request containing "check",
  "verify" or "match" straight to `verify_claim_against_source`.
- **C.** Expand both tool descriptions with more edge cases, including example requests that
  contain the word "check".
- **D.** Rewrite the system-prompt instruction so that it no longer ties checking to
  extracting data points, and leave the tool descriptions unchanged.

**Answer: D**

**Evidence in the stem.**
- The descriptions are already detailed and differentiated, so missing information is ruled out.
- The failure correlates with one **keyword**, and requests without it route correctly.
- The system prompt ties that exact keyword to extracting data points.

**Why D wins.** Tool descriptions are the main way the model selects a tool, but system-prompt
wording is read too, and a keyword-sensitive instruction can create a tool association that
overrides a good description. The objective asks you to review system prompts for exactly
this. The cause is one sentence, and removing it fixes the routing at its root.

**Why the others are attractive, and still wrong.**
- **A** treats a cause problem as a decision-boundary problem. The examples add tokens on every
  turn and fight the instruction instead of removing it. The conflicting sentence is still there.
- **B** rebuilds the failure on purpose: a keyword rule, now in code, that bypasses the model's
  language understanding. "Check the formatting of these tables" would be sent to
  verification.
- **C** reaches for the right mechanism in the wrong place. Descriptions are the first fix when
  they are minimal or overlapping. Here they are already clear, so more description text does
  not touch the instruction that causes the misroute.

**The question to ask:** what does the evidence say is missing? Here nothing is missing;
something is pulling the wrong way.

---

## Item 3: Code Generation with Claude Code

*Domain 3, Claude Code Configuration and Workflows. Task 3.3.*

Your team uses Claude Code in a monorepo. React test files (`*.test.tsx`) sit next to the
components they test, in about 40 directories. The team wants Claude Code to apply its testing
conventions (Testing Library queries, no snapshot tests) automatically whenever it edits a test
file. These conventions should not take up context while it works on other code.

What should you do?

- **A.** Create `.claude/rules/testing.md` with `paths: ["**/*.test.tsx"]` in its YAML
  frontmatter, holding the conventions.
- **B.** Add a `CLAUDE.md` file with the testing conventions to each of the 40 directories that
  contain test files.
- **C.** Put the conventions in a `testing-conventions` skill and ask developers to invoke it
  before writing tests.
- **D.** Move the conventions into `standards/testing.md` and import it from the root
  `CLAUDE.md` with `@standards/testing.md`.

**Answer: A**

**Evidence in the stem.**
- "sit next to the components ... in about 40 directories": the convention follows a **file
  type**, not a folder.
- "automatically": loading must not depend on anyone remembering.
- "should not take up context while it works on other code": it has to load conditionally.

**Why A wins.** A rule file in `.claude/rules/` with a `paths` glob loads only when Claude Code
works on a matching file. `**/*.test.tsx` matches test files wherever they live. It is one file
to maintain, it applies automatically, and it costs no context elsewhere.

**Why the others are attractive, and still wrong.**
- **B** works, and directory-level `CLAUDE.md` is a real, sensible mechanism. But it is the
  wrong shape: 40 copies to keep in sync, and the 41st directory with a test file is missed
  until someone remembers. Directory files follow folders; globs follow file types.
- **C** keeps the conventions out of context, but a skill loads on invocation. "Ask developers
  to invoke it" is the opposite of automatic.
- **D** looks modular, and `@path` imports are good for organising ownership. But an import
  expands inline when the session starts and loads in full every time, so it saves no context.
  Only `paths:` frontmatter loads conditionally.

**The shapes to remember:** a convention that follows a file type is a `paths` glob; one that
follows a folder is a subdirectory `CLAUDE.md`; one that follows a task is a skill.
