# CCAR-F quiz bank

Thirty original exam-style items, one per official task statement, written against the task's
objectives in the CCAR-F exam guide. None is copied from the exam guide or any exam.

Format of every item:

- **Header:** `Q-<task>` and the task title.
- **Meta:** domain, scenario, type (single choice, or choose two).
- **Stem and options:** show these to the user exactly as written.
- **Answer, Evidence, Why it wins, Why the others fail, Learn more:** show only after the
  user has answered.

---

## Q-1.1 Agentic loops for autonomous task execution

**Meta:** Domain 1, Agentic architecture and orchestration | Scenario: Developer Productivity
with Claude | Type: single choice

Before switching to the Agent SDK's built-in loop, your team writes its own agentic loop over
the Messages API for a tool that helps engineers explore unfamiliar codebases. After each
response, the loop runs any requested tools and appends the results, and it exits as soon as a
response contains a text block. Engineers report runs that stop half-way. In the logs, the last
response holds the text "Next I'll read the config loader" and a `tool_use` block for `Read`,
and that tool never ran. Run length varies widely: some questions need two tool calls, others
more than thirty.

How should the loop decide whether to continue?

- **A.** Tell Claude in the system prompt to end its final answer with the word DONE, and exit
  only when the response text contains it.
- **B.** Continue while `stop_reason` is `"tool_use"`, appending the assistant message and a
  `tool_result` for each `tool_use` block; stop when `stop_reason` is `"end_turn"`, and keep an
  iteration cap only as a safety net.
- **C.** Ignore the text and run a fixed 15 iterations per question, which covers most of the
  runs seen in testing.
- **D.** Replace the loop with a fixed sequence of Glob, Grep and Read, so every run finishes
  after the same three steps.

**Answer:** B

**Evidence:** the last response carried text and a `tool_use` block together, so "contains
text" fired while work was still pending. "Two tool calls" to "more than thirty" means no fixed
count or fixed sequence fits every run.

**Why it wins:** `stop_reason` is a protocol field with defined values. `"tool_use"` means
Claude wants a tool run and its result appended for the next iteration; `"end_turn"` means it
has finished. A cap is still worth having, as a guard against runaway loops, not as the exit.

**Why the others fail:**
- **A:** parses natural language to decide termination. Prose is generated content, not a
  control channel: the model can say DONE early or finish without it.
- **C:** an iteration cap as the primary stopping mechanism. It cuts off the thirty-step runs
  and has nothing to do with whether the task is finished.
- **D:** a pre-configured tool sequence. It throws away model-driven decisions, which is the
  reason to have a loop when the questions vary this much.

**Note:** the exam phrases termination as "end_turn"; shipped code usually exits on
`stop_reason != "tool_use"`, which also covers `max_tokens` and `stop_sequence`.

**Learn more:** https://code.claude.com/docs/en/agent-sdk/overview

---

## Q-1.2 Multi-agent orchestration with coordinator-subagent patterns

**Meta:** Domain 1, Agentic architecture and orchestration | Scenario: Multi-Agent Research
System | Type: single choice

Your coordinator researches "the effect of heat pumps on household energy bills in Europe". It
assigns three subtopics to the search and analysis subagents: installation costs, running costs
and government subsidies. Every subagent completes without errors. The synthesis is thorough on
costs, but its subsidies section rests on two sources from a single country, and the synthesis
subagent remarks that it found little on other countries' schemes. Today the coordinator passes
the synthesis straight to the report subagent.

What should you change?

- **A.** Give the synthesis subagent the web search tools, so it can find more sources itself
  whenever a section is thin.
- **B.** Let the synthesis subagent send follow-up queries directly to the search subagent and
  wait for its results.
- **C.** Run the whole pipeline three times with the original assignments and merge the three
  syntheses.
- **D.** Have the coordinator check the synthesis for gaps, re-delegate targeted queries (for
  example, subsidy schemes in other European countries) to search and analysis, and re-invoke
  synthesis until coverage is sufficient.

**Answer:** D

**Evidence:** subsidies were assigned and every subagent succeeded, so the decomposition and
the execution are not at fault. The gap only becomes visible in the synthesis, and the
coordinator currently forwards that synthesis without evaluating it.

**Why it wins:** this is the iterative refinement loop the coordinator owns. It evaluates the
synthesis for gaps, sends narrow queries aimed at the gap, and re-invokes synthesis, stopping on
sufficient coverage rather than after a fixed number of rounds.

**Why the others fail:**
- **A:** dissolves the role boundary. Giving synthesis the full search toolset breaks least
  privilege and separation of concerns; the coordinator should route the extra research.
- **B:** spoke-to-spoke communication. It bypasses the coordinator, losing observability,
  consistent error handling and control over what each subagent sees.
- **C:** not targeted. Re-running the same assignments repeats the same thin search, burns
  tokens on duplicate findings, and stops after a fixed count instead of on coverage.

**Learn more:** https://code.claude.com/docs/en/agent-sdk/subagents

---

## Q-1.3 Subagent invocation, context passing and spawning

**Meta:** Domain 1, Agentic architecture and orchestration | Scenario: Multi-Agent Research
System | Type: choose two

A coordinator built with the Claude Agent SDK researches a topic with three search subagents
and then a synthesis subagent. Two problems show up in testing. Runs are slow, because the
coordinator spawns the three searchers one after another, one per turn. And the final report
cites sources inconsistently: the synthesis subagent's prompt says "write the report from the
search results gathered earlier", and some citations point to documents no searcher found.

Which two changes fix these problems?

- **A.** Give the coordinator a step-by-step procedure that names each searcher, its query and
  the order to run them in.
- **B.** Have the coordinator emit all three search subagent calls in a single response.
- **C.** Rely on the synthesis subagent inheriting the coordinator's conversation, and remove
  the duplicate findings from its prompt.
- **D.** Put the complete search findings into the synthesis subagent's prompt as structured
  records that keep each claim with its source URL and document name.
- **E.** Spawn the synthesis subagent before the searchers so it can watch their results
  arrive.

**Answer:** B and D

**Evidence:** "one after another, one per turn" is a parallelism problem. "the search results
gathered earlier" points to context the synthesis subagent never received, and invented
citations are what an agent produces when attribution is missing.

**Why it wins:**
- **B:** parallel subagents are spawned by emitting several subagent (`Task`) calls in one
  coordinator response; one per turn is correct but slow.
- **D:** a subagent sees only what its prompt contains. Passing complete findings as
  structured records keeps each claim tied to its source, so attribution survives synthesis.

**Why the others fail:**
- **A:** reads like rigour, but the guide wants coordinator prompts that state goals and
  quality criteria; a fixed procedure removes adaptability and fixes neither problem.
- **C:** the tempting misconception. Subagents do not inherit the coordinator's conversation;
  the prompt is the only channel from parent to child.
- **E:** a subagent cannot watch other subagents; nothing reaches it outside its prompt.

**Note:** the exam calls the spawning tool `Task`, and a coordinator's `allowedTools` must
include it. Current Claude Code releases have renamed it `Agent`; `Task` is still accepted.

**Learn more:** https://code.claude.com/docs/en/agent-sdk/subagents

---

## Q-1.4 Multi-step workflows with enforcement and handoff

**Meta:** Domain 1, Agentic architecture and orchestration | Scenario: Customer Support
Resolution Agent | Type: choose two

Your support agent escalates billing disputes it cannot resolve by calling
`escalate_to_human`, whose only input is a free-text `note`. Human agents work in a case tool
that shows the escalation's fields but cannot display chat transcripts. Two problems come up.
Human agents spend the first minutes of each case asking customers to repeat details the agent
had already established. And cases are routed by refund amount to staff with the right approval
limit, but about one handoff in fifteen states no amount, so those cases land in the wrong
queue. Every case must arrive with an amount.

Which two changes fix these problems?

- **A.** Change `escalate_to_human` to take a structured handoff record: customer ID, root
  cause, refund amount, recommended action and the actions already taken.
- **B.** Attach the full conversation transcript to every escalation, so the human agent can
  read everything that was said.
- **C.** Add to the system prompt: "Always state the refund amount when you escalate."
- **D.** Ask the agent to write a longer, more detailed prose summary of the conversation in
  the `note` field.
- **E.** Add a `PreToolUse` hook on `escalate_to_human` that denies a handoff with no refund
  amount, with a reason telling the agent to add the amount and call the tool again.

**Answer:** A and E

**Evidence:** "cannot display chat transcripts" means the handoff is the human's entire
context. "Routed by refund amount" needs a field code can read, and "every case must arrive
with an amount" is a guarantee, not a preference.

**Why it wins:**
- **A:** the structured handoff carries the four fields the human needs (customer ID, root
  cause, refund amount, recommended action), plus what was already tried, so nobody re-asks
  the customer. Separate fields can be routed on.
- **E:** a hook makes completeness deterministic. A handoff without an amount never reaches the
  queue, and the denial reason is fed back to the agent, so it adds the amount and retries.

**Why the others fail:**
- **B:** the case tool cannot show transcripts, and a transcript is neither routable nor
  checkable for a missing amount.
- **C:** prompt-based guidance is probabilistic. It lowers the one-in-fifteen rate but cannot
  guarantee "every case".
- **D:** more prose is still prose: code cannot route on it or check it for the field it left
  out.

**Learn more:** https://code.claude.com/docs/en/agent-sdk/hooks

---

## Q-1.5 Agent SDK hooks for interception and data normalisation

**Meta:** Domain 1, Agentic architecture and orchestration | Scenario: Customer Support
Resolution Agent | Type: single choice

Your support agent decides whether orders fall inside the 30-day return window. `lookup_order`
comes from a vendor's MCP server and returns `delivered_at` as a Unix timestamp. Your
carrier-tracking MCP tool returns dates such as "02/03/2026", and a third tool returns ISO 8601
strings. Order status arrives as numeric codes from one tool and as words from another. The
system prompt already explains every format, yet the agent still misjudges return eligibility
in a small share of cases. You cannot change the vendor's server, and none of the tools accepts
a date-format parameter.

What should you do?

- **A.** Add worked examples to the system prompt that convert each date format and status code
  before the dates are compared.
- **B.** Add a `PreToolUse` hook on the three tools that rewrites their input to request ISO
  8601 dates.
- **C.** Add a `PostToolUse` hook matching the three tools that converts every date to ISO 8601
  and every status code to a named label, returning the result as `updatedToolOutput` before
  the agent sees it.
- **D.** Change each MCP server to return ISO 8601 dates and named statuses, starting with your
  own carrier-tracking tool.

**Answer:** C

**Evidence:** "the system prompt already explains every format, yet" rules out more prompting.
"You cannot change the vendor's server" rules out fixing the tools, and "none of the tools
accepts a date-format parameter" rules out changing the request.

**Why it wins:** this is a data problem, not a reasoning problem. A `PostToolUse` hook runs on
the result before the model processes it, so one deterministic conversion covers every matching
tool, including third-party servers you do not own.

**Why the others fail:**
- **A:** still prompt-based and probabilistic; it moves the error rate without removing the
  class of error, and costs tokens on every turn.
- **B:** `PreToolUse` acts on the outgoing call, and there is no parameter to rewrite. The
  formats come back in the result, which is `PostToolUse`'s job.
- **D:** impossible for the vendor's server, and N fixes in N places instead of one hook.

**Learn more:** https://code.claude.com/docs/en/agent-sdk/hooks

---

## Q-1.6 Task decomposition strategies for complex workflows

**Meta:** Domain 1, Agentic architecture and orchestration | Scenario: Claude Code for
Continuous Integration | Type: single choice

Your CI pipeline runs Claude Code on every pull request to the payments service. Each review
must cover the same four aspects: input validation, error handling, personal data in logs, and
changes to the public API contract. Today a single prompt says "Review this pull request
thoroughly" and the agent plans its own investigation. On two re-runs of the same 200-line pull
request, one review covered all four aspects and the other never checked the logging. Your
compliance team needs every review to cover the same aspects, reproducibly.

What should you change?

- **A.** Replace the single prompt with a fixed chain: one focused step per aspect, run in the
  same order on every pull request and each given the diff, then a final step that combines
  the findings.
- **B.** Keep the self-planned review, but have the agent first map the service's structure and
  prioritise the highest-risk files before it starts.
- **C.** Move the review to a model with a larger context window, so all four aspects fit in a
  single pass.
- **D.** List the four aspects in the prompt and ask the agent to confirm in its summary that it
  checked each one.

**Answer:** A

**Evidence:** "the same four aspects" on every pull request means the steps are known before
the run starts, and "reproducibly" asks for identical structure every time. A 200-line diff is
small, so size is not the problem.

**Why it wins:** prompt chaining is the pattern for predictable multi-aspect reviews. Each step
has one job, so no aspect competes with the others for attention, and the step list is the same
on every run.

**Why the others fail:**
- **B:** map-first adaptive decomposition is for open-ended investigation where the subtasks
  are not known in advance. Here they are, and an adaptive plan is what produced the variation.
- **C:** fitting is not attending. A 200-line diff already fits; a bigger window does not make
  one pass weigh four concerns evenly.
- **D:** still one pass balancing four jobs, and a self-reported checklist is prompt-based, so
  a run can still skip an aspect and report that it checked it.

**Learn more:** https://code.claude.com/docs/en/agent-sdk/overview

---

## Q-1.7 Session state, resumption and forking

**Meta:** Domain 1, Agentic architecture and orchestration | Scenario: Developer Productivity
with Claude | Type: single choice

An engineer spent most of a day in a Claude Code session named `ledger-analysis`, mapping a
legacy ledger service: its modules, call paths and test gaps. Nobody has changed the code
since. The team now wants to compare two refactoring approaches, extracting a repository layer
and moving to event sourcing, each explored in depth from the same analysis and neither
influenced by the other. The original analysis must also stay available for a third approach
next week.

How should the engineer set this up?

- **A.** Resume `ledger-analysis`, explore the repository layer, then continue in the same
  session with event sourcing.
- **B.** Resume `ledger-analysis` with `--fork-session` once for each approach, so each branch
  gets its own session ID and the original session stays unchanged.
- **C.** Start two new sessions, each seeded with a structured summary of the analysis, because
  a summary is more reliable than resumed context.
- **D.** Start two new sessions and re-run the full codebase analysis in each, so both
  approaches start from fresh tool results.

**Answer:** B

**Evidence:** "nobody has changed the code since" means the prior tool results are still
valid. "Neither influenced by the other" and "must stay available" rule out working both
approaches in one session.

**Why it wins:** forking creates independent branches from a shared baseline. Each branch
inherits the full analysis up to the branch point, then diverges, and the baseline is untouched,
so next week's third approach can fork from it too.

**Why the others fail:**
- **A:** the second approach inherits the first one's reasoning, and the baseline session is
  changed by both explorations.
- **C:** starting fresh with a summary is the answer when prior tool results are stale. Here
  they are valid, so a summary only throws away detail the expensive analysis produced.
- **D:** re-running the analysis is correct but wasteful. The analysis is the expensive part,
  and forking reuses it.

**Note:** the exam treats `--resume <session-name>` as resuming by name; current Claude Code
uses the name as a search term for the session picker, so a script resumes by session ID.

**Learn more:** https://code.claude.com/docs/en/agent-sdk/sessions

---

## Q-2.1 Tool interfaces with clear descriptions and boundaries

**Meta:** Domain 2, Tool design and MCP integration | Scenario: Customer Support Resolution
Agent | Type: single choice

Your support agent, built with the Claude Agent SDK, has a custom MCP tool `account_lookup`. It
takes a `customer_id` and a `view` enum (`profile`, `billing_history`, `open_disputes`) and
returns a differently shaped result for each view. Last sprint the team expanded its
description to explain all three views, with example queries for each. The agent still asks
for the wrong view: for "why was I charged twice in March?" it often requests `profile` and
answers from the wrong data. No other tool in the agent's set returns customer data.

What is the most effective fix?

- **A.** Add six few-shot examples to the system prompt that map billing, dispute and profile
  questions to the right `view` value.
- **B.** Replace it with `get_customer_profile`, `get_billing_history` and
  `list_open_disputes`, each with its own input schema, output shape and a description that
  says when to use it rather than the other two.
- **C.** Rename `account_lookup` to `get_customer_account_details` and rewrite its description
  around the account domain.
- **D.** Add a pre-processing step that sets `view` from keywords in the customer's message,
  such as "charged" or "dispute", before the agent runs.

**Answer:** B

**Evidence:** "expanded its description ... with example queries" means the first fix has
already been tried. "No other tool ... returns customer data" means there is no neighbour to
collide with. What is left is one tool doing three jobs with three output shapes under one
vague name.

**Why it wins:** a generic tool that does several jobs is not a contract. Splitting it into
purpose-specific tools gives each one a single job, a defined input and a defined output, and
a description that can say when to use it instead of its siblings, so the choice becomes
determinate. The cost is a longer tool list, which is why splitting comes after expanding
descriptions, not before.

**Why the others fail:**
- **A:** few-shot examples add tokens on every turn and leave the root cause in place: three
  jobs still share one tool and one description.
- **C:** renaming removes overlap between two similar tools. Here there is no second tool; the
  new name is still one name for three jobs.
- **D:** a keyword routing layer is over-engineered and bypasses the model's language
  understanding. "I was charged for a dispute fee" would match both keywords.

**Learn more:** https://code.claude.com/docs/en/agent-sdk/custom-tools

---

## Q-2.2 Structured error responses for MCP tools

**Meta:** Domain 2, Tool design and MCP integration | Scenario: Developer Productivity with
Claude | Type: single choice

Your team's MCP server exposes `search_tickets` to an internal engineering agent. When the
ticketing API times out, the tool catches the exception and returns `{"results": []}` as a
normal result. Engineers report that the agent sometimes tells them "there are no open tickets
for this service" when there are dozens.

What is the best fix?

- **A.** Add to the agent's system prompt: "If a search returns no results, run it again
  before answering."
- **B.** Return the text "Operation failed" with `isError: true` whenever anything goes wrong in
  the tool.
- **C.** In the tool, retry the timeout itself; if it still fails, return `isError: true` with
  `errorCategory: "transient"`, `isRetryable: true` and what was attempted, and keep empty
  results only for searches that genuinely matched nothing.
- **D.** Let the timeout exception propagate so the agent's whole run stops with an error.

**Answer:** C

**Evidence:** "returns `{"results": []}` as a normal result" on a timeout: a failure is being
reported as a successful empty search, so the agent cannot tell "nothing found" from "could
not look".

**Why it wins:** the tool knows a timeout is transient, so it retries locally, then reports
what is left as a structured error the agent can act on. An empty list stays reserved for a
query that succeeded and matched nothing.

**Why the others fail:**
- **A:** probabilistic, and it retries genuine empty results too. The defect is in the tool's
  response, not in the agent's judgement.
- **B:** `isError` is right, but a generic "Operation failed" hides whether a retry can help,
  so the agent cannot choose a recovery.
- **D:** one transient failure should not end the whole workflow when a retry or a partial
  answer could still succeed.

**Learn more:** https://modelcontextprotocol.io/docs/learn/architecture

---

## Q-2.3 Tool distribution across agents and tool_choice

**Meta:** Domain 2, Tool design and MCP integration | Scenario: Structured Data Extraction |
Type: choose two

Your pipeline sends each scanned document to Claude with four tools: `detect_language`,
`extract_invoice`, `extract_receipt` and `extract_contract`, all on `tool_choice: auto`. The
document type is not known in advance. Two problems show up. About one document in fifteen
skips `detect_language` and goes straight to extraction, so dates and amounts are parsed with
the wrong locale rules. And about 4% of responses are prose, such as "This appears to be a
supplier invoice", with no tool call at all, which your parser rejects.

Which two changes fix these problems?

- **A.** Set `tool_choice` to `{"type": "tool", "name": "extract_invoice"}` on every request,
  so the parser always receives a tool call.
- **B.** Keep `auto` and add to the system prompt: "Always call `detect_language` first, and
  never reply in plain text."
- **C.** On the first request, set `tool_choice` to `{"type": "tool", "name":
  "detect_language"}`, then run the extraction step in a follow-up turn that carries its
  result.
- **D.** Add a classifier that predicts the document type and enables only the matching
  extraction tool on each request.
- **E.** On the extraction request, set `tool_choice` to `{"type": "any"}`.

**Answer:** C and E

**Evidence:** "skips `detect_language`" is a step that must come first and sometimes does not.
"prose ... with no tool call at all" is the model using its option to answer in text. "not
known in advance" rules out forcing any one extraction tool.

**Why it wins:**
- **C:** forced selection guarantees that this request calls `detect_language`. Because
  `tool_choice` applies per request, the remaining steps are processed in follow-up turns.
- **E:** `any` guarantees that Claude calls a tool rather than returning conversational text,
  while still letting it choose which extraction schema fits the unknown document type.

**Why the others fail:**
- **A:** forcing a specific tool guarantees a call, but always the invoice schema; receipts and
  contracts would be pushed into the wrong shape.
- **B:** a prompt instruction is probabilistic. It lowers both rates; it does not remove
  either failure.
- **D:** a classifier changes which tools are available, not whether a tool is called or in
  what order. With `auto` the model can still answer in prose and still skip
  `detect_language`.

**Note:** on some newer model families the API rejects `any` and forced `tool` values; the
exam's answer is unchanged.

**Learn more:** https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview

---

## Q-2.4 MCP servers in Claude Code and agent workflows

**Meta:** Domain 2, Tool design and MCP integration | Scenario: Developer Productivity with
Claude | Type: single choice

Your team's agent, built with the Claude Agent SDK, helps engineers operate a legacy platform.
A custom MCP server exposes `search_runbooks` and `get_runbook`. Traces show that on almost
every task the agent makes five to eight `search_runbooks` calls with guessed terms, just to
learn which runbooks and service areas exist, before its first useful `get_runbook` call. The
set of runbooks changes about once a week. The agent always picks the MCP tools rather than
the built-in tools.

What is the best way to cut these exploratory calls?

- **A.** Expand the `search_runbooks` description with its capabilities and output fields, so
  the agent stops preferring `Grep`.
- **B.** Set `tool_choice` to `{"type": "tool", "name": "get_runbook"}` on the first request
  of each task.
- **C.** Add a `list_runbooks` tool that returns every runbook id and title, and describe it
  as the first call to make on each task.
- **D.** Expose the runbook catalogue (ids, titles and service areas) as an MCP resource that
  the application reads and gives the agent at the start of each task.

**Answer:** D

**Evidence:** "just to learn which runbooks and service areas exist" is the agent mapping the
data by trial and error. "On almost every task" means the map is always needed, and "always
picks the MCP tools" rules out a description contest with the built-ins.

**Why it wins:** MCP resources expose content catalogues so the agent can see what data exists
without exploratory tool calls. A resource is app-controlled: the application fetches it and
injects it, so the agent starts with the map and its first tool call is already the right
one.

**Why the others fail:**
- **A:** enhancing an MCP description is the fix when the agent prefers a built-in such as
  `Grep`. The stem says it already uses the MCP tools.
- **B:** forcing `get_runbook` guarantees a call, not a correct one. Without the map, the
  agent has to guess the runbook id.
- **C:** the closest distractor. It delivers the same data as a tool, so the model still has
  to decide to call it and every task still pays a round trip. When the map is needed on
  almost every task, the application should provide it.

**Learn more:** https://modelcontextprotocol.io/docs/learn/architecture

---

## Q-2.5 Built-in tools: Read, Write, Edit, Bash, Grep, Glob

**Meta:** Domain 2, Tool design and MCP integration | Scenario: Developer Productivity with
Claude | Type: single choice

An engineer asks your codebase agent to find every caller that would break if the signature
of `parse_amount` in `billing/money.py` changes. Most services do not import from
`billing/money.py` directly: `billing/__init__.py` re-exports the module's functions, and
exposes `parse_amount` under a second name, `to_minor_units`, for older code. The agent's
first search, a Grep for `from billing.money import`, found four callers. The engineer knows
of at least a dozen more.

What should the agent do next?

- **A.** Read `billing/__init__.py` to list every name it exports for `parse_amount`, then
  Grep the codebase for each of those names.
- **B.** Glob for `**/*.py` and Read every matching file, so that no caller is missed.
- **C.** Grep the codebase for `parse_amount`, which finds every call to the function
  wherever it is imported from.
- **D.** Run `grep -rn "billing" .` through Bash to catch every reference to the package.

**Answer:** A

**Evidence:** "re-exports" and "under a second name, `to_minor_units`": the symbol's real usage
hides behind the wrapper module, so a search for the original path or the original name
undercounts.

**Why it wins:** tracing usage through a wrapper module is two steps: first identify every
name the wrapper exports, then search for each name across the codebase. Read (or a narrow
Grep for exports) handles step one; a Grep per name handles step two.

**Why the others fail:**
- **B:** reading every file up front fills the context window with irrelevant code. Build
  understanding incrementally: search to find where to look, then read.
- **C:** a single search on the original symbol misses every caller that uses the alias
  `to_minor_units`.
- **D:** search belongs to the Grep tool, not to `grep` through Bash; Bash is for what must
  execute. The pattern also matches every unrelated mention of "billing".

**Note:** current Claude Code releases on macOS, Linux and WSL leave Glob and Grep out of the
default tool set and search with `grep` through Bash; the exam's answer is still the Grep tool.

**Learn more:** https://code.claude.com/docs/en/common-workflows

---

## Q-3.1 CLAUDE.md hierarchy, scoping and modular organisation

**Meta:** Domain 3, Claude Code configuration and workflows | Scenario: Code Generation with
Claude Code | Type: single choice

Your monorepo has three packages: `billing-api`, `admin-ui` and `mobile-sdk`. The security
team owns `standards/secrets-handling.md`, the platform team owns `standards/api-conventions.md`
and the design-system team owns `standards/react-patterns.md`. Today each package's
`CLAUDE.md` holds pasted copies of the sections its maintainers think apply, and the copies
have drifted: `billing-api` still tells Claude to log full request bodies, which the security
team banned two months ago. Each standards file should live in one place, edited by its
owners, and each package's maintainers should keep choosing which standards apply to their
code.

What should you do?

- **A.** Delete the package files and move the content of all three standards files into the
  root `CLAUDE.md`, so every package always sees the current version.
- **B.** Move the three standards files into `.claude/rules/` without frontmatter, so they
  load as topic files alongside `CLAUDE.md`.
- **C.** Replace the pasted copies with `@path` imports in each package's `CLAUDE.md`, such as
  `@../../standards/secrets-handling.md`, listing only the standards that package's
  maintainers choose.
- **D.** Ask each package's maintainers to put the standards that apply to them in their own
  `~/.claude/CLAUDE.md`.

**Answer:** C

**Evidence:** "pasted copies ... have drifted" is a duplication problem, "live in one place,
edited by its owners" asks for a single source, and "maintainers should keep choosing which
standards apply" asks for per-package selection.

**Why it wins:** a line with `@` followed by a path is expanded inline at launch, and a
relative path resolves against the file that contains it. Each package's `CLAUDE.md` imports
only the standards its maintainers judge relevant, while each standards file is maintained
once by the team that owns it, so a fix like the logging ban reaches every importer.

**Why the others fail:**
- **A:** one source, but it takes the choice away from the package maintainers: every
  package gets every team's rules, and the root file grows into the monolith the split was
  avoiding.
- **B:** a rule file without frontmatter loads always, for every package, so this also
  removes the per-package choice. Topic files help people find rules; they do not select
  them per package.
- **D:** `~/.claude/CLAUDE.md` is in each developer's home directory, not in version control,
  so teammates and new joiners never receive it.

**Note:** imports organise ownership; they are not a context saving. Everything imported still
loads in full. The exam calls this "the @import syntax", but there is no `import` keyword: the
syntax is `@` directly followed by a path.

**Learn more:** https://code.claude.com/docs/en/memory

---

## Q-3.2 Custom slash commands and skills

**Meta:** Domain 3, Claude Code configuration and workflows | Scenario: Code Generation with
Claude Code | Type: choose two

Your team has a project skill at `.claude/skills/dep-audit/SKILL.md` that scans every package
manifest and lists outdated dependencies, licence data and security advisories. Two
complaints have come in. After `/dep-audit` runs, the session holds several hundred lines of
scan output, and Claude loses track of the feature the developer was building. Separately, one
developer wanted extra licence checks for their own work, so they copied the skill to
`~/.claude/skills/dep-audit/` and edited it. Since then they no longer get the fixes
teammates push to the team's skill.

Which two changes fix these problems?

- **A.** Add to `SKILL.md`: "Summarise the findings in ten lines before displaying them."
- **B.** Add `context: fork` to the team skill's frontmatter.
- **C.** Add `allowed-tools: ["Read", "Grep", "Glob"]` to the team skill's frontmatter.
- **D.** Add `override: false` to the team skill's frontmatter, so personal copies cannot
  replace it.
- **E.** Rename the personal copy to a different name, such as
  `~/.claude/skills/dep-audit-licences/`.

**Answer:** B and E

**Evidence:** "several hundred lines of scan output" and "loses track of the feature" are
verbose skill output flooding the main conversation. "copied the skill to
`~/.claude/skills/dep-audit/`" under the same name, followed by "no longer gets the fixes",
is a personal skill shadowing the project one.

**Why it wins:**
- **B:** `context: fork` runs the skill in an isolated sub-agent context, so its working
  output never enters the main conversation; only the result comes back.
- **E:** personal skills in `~/.claude/skills/` take precedence over project skills with the
  same name. A different name keeps the team's `/dep-audit` working for them and gives them a
  separate `/dep-audit-licences`.

**Why the others fail:**
- **A:** the model still generates and holds the full scan in the main context on its way to
  the summary; isolation, not an instruction, keeps it out.
- **C:** `allowed-tools` restricts what the skill can touch while it runs. Nothing destructive
  happened, and a read-only skill can produce just as much output.
- **D:** there is no `override` frontmatter key; it is an invented mechanism.

**Learn more:** https://code.claude.com/docs/en/skills

---

## Q-3.3 Path-specific rules for conditional convention loading

**Meta:** Domain 3, Claude Code configuration and workflows | Scenario: Code Generation with
Claude Code | Type: single choice

Last quarter your team split a 600-line `CLAUDE.md` into topic files under `.claude/rules/`:
`typescript.md`, `testing.md` and `terraform.md`, none with frontmatter. Developers now find
and update rules easily. But `terraform.md` holds 150 lines of module and state-locking
conventions, and they are loaded in every session, including React bug fixes that never touch
infrastructure. All Terraform code lives under `terraform/`. The conventions must still apply
automatically whenever Claude Code edits a Terraform file.

What should you do?

- **A.** Move the conventions to `standards/terraform.md` and reference it from the root
  `CLAUDE.md` with `@standards/terraform.md`.
- **B.** Fold `terraform.md` back into the root `CLAUDE.md` under the heading "Terraform:
  apply only when editing files in terraform/".
- **C.** Turn `terraform.md` into a skill whose description mentions Terraform, so Claude
  invokes it when the work is about infrastructure.
- **D.** Add YAML frontmatter with `paths: ["terraform/**/*"]` to `.claude/rules/terraform.md`.

**Answer:** D

**Evidence:** "none with frontmatter" and "loaded in every session, including React bug fixes"
show the split bought maintainability but no conditional loading. "apply automatically
whenever Claude Code edits a Terraform file" asks for activation tied to the file, not to
anyone's choice.

**Why it wins:** a `.claude/rules/` file with a `paths` field loads only when Claude Code
works on a file matching one of its globs. Adding the frontmatter turns the existing topic
file into a conditional one, so React sessions stop paying for Terraform conventions and
Terraform edits still get them.

**Why the others fail:**
- **A:** `@path` imports expand inline at launch, so the 150 lines still load in every
  session; the content has moved, not the cost.
- **B:** still loaded every session, and it relies on Claude inferring which section applies
  instead of matching the file being edited.
- **C:** a skill loads on invocation or a description match, which is the model's choice, not
  the deterministic "automatically" the stem requires.

**Learn more:** https://code.claude.com/docs/en/memory

---

## Q-3.4 Plan mode versus direct execution

**Meta:** Domain 3, Claude Code configuration and workflows | Scenario: Code Generation with
Claude Code | Type: single choice

Your team asks Claude Code to replace a home-grown logging module with a standard library
across about 60 files in three services. There are two viable approaches: wrap the new library
behind the existing interface, or call it directly everywhere. The second needs a change to
the log shipping configuration in production.

How should the developer run this task?

- **A.** Use plan mode to explore the codebase and compare the two approaches, approve a plan,
  then let Claude Code execute it.
- **B.** Use direct execution, and switch to plan mode if the migration turns out to be
  complicated.
- **C.** Use direct execution with extended thinking enabled, so Claude reasons more carefully
  about each file as it edits it.
- **D.** Ask the Explore subagent to make the changes, so the edits do not fill the main
  conversation's context.

**Answer:** A

**Evidence:** "about 60 files in three services", "two viable approaches" and a production
configuration change: large scope, a real design decision and infrastructure consequences.

**Why it wins:** plan mode is for multi-file changes with several valid approaches and
architectural implications. It explores and produces a plan to approve before anything is
written; then the approved plan is executed directly.

**Why the others fail:**
- **B:** the complexity is already stated in the scenario; "switch if it gets complicated"
  is the classic wrong answer when the stem has described it.
- **C:** extended thinking is depth on one problem, not a way to choose an approach across
  60 files before changing them.
- **D:** Explore isolates verbose discovery and returns summaries; it is not the tool for
  making the changes, and it does not decide between the approaches.

**Learn more:** https://code.claude.com/docs/en/common-workflows

---

## Q-3.5 Iterative refinement for progressive improvement

**Meta:** Domain 3, Claude Code configuration and workflows | Scenario: Code Generation with
Claude Code | Type: single choice

Claude Code has written a client for a partner's rate-limited API, used by a sync job with a
five-minute deadline. Your review finds three problems. The retry loop retries HTTP 429
responses immediately instead of honouring the `Retry-After` header. The 10-second
per-request timeout is too short for the back-off the retry policy will need. And nothing
stops retries from running past the job's deadline. The back-off schedule decides how long a
request can take, the timeout must allow for it, and both must fit inside the deadline.

How should you give Claude this feedback?

- **A.** In a single detailed message, describe all three problems and how they constrain
  one another, and ask for one coherent change.
- **B.** Send one problem per iteration and verify each fix before raising the next, so any
  regression can be traced to a single change.
- **C.** Before changing anything, ask Claude to explain its current understanding of the
  retry and timeout requirements.
- **D.** Rewrite the original requirements in more precise prose, with exact values for every
  setting, and ask Claude to regenerate the whole client.

**Answer:** A

**Evidence:** "The back-off schedule decides how long a request can take, the timeout must
allow for it, and both must fit inside the deadline": the three fixes interact.

**Why it wins:** when fixes interact, all the issues go in one detailed message so Claude
reasons about them together and produces one coherent change, instead of a fix that the next
one undoes.

**Why the others fail:**
- **B:** sequential iteration is the right choice for independent issues. Here it causes
  churn: fixing the back-off breaks the timeout, and fixing the timeout breaks the deadline.
- **C:** asking Claude to explain its understanding diagnoses a misread, costs a round trip,
  and still leaves you to describe the fixes. The problems are already known.
- **D:** more precise prose is the remedy people reach for when prose is misread; nothing was
  misread here, and regenerating the client discards the working parts of the code.

**Learn more:** https://code.claude.com/docs/en/common-workflows

---

## Q-3.6 Claude Code in CI/CD pipelines

**Meta:** Domain 3, Claude Code configuration and workflows | Scenario: Claude Code for
Continuous Integration | Type: single choice

Your pipeline pipes each pull request's diff into `claude -p` with a review prompt. A Python
script then uses regular expressions to pull the file, line, severity and message out of the
text, and posts each finding as an inline PR comment. About one run in ten posts nothing:
Claude opened with a sentence of preamble, or wrote line ranges in a different shape. The team
wants every run to produce findings the poster can read without guessing at the format.

What should you change?

- **A.** Add to the review prompt: "Respond only with a JSON array of findings, each with
  file, line, severity and message, and no other text."
- **B.** Run with `--output-format json` and `--json-schema`, using a schema for a `findings`
  array of objects with `file`, `line`, `severity` and `message`, and have the poster read
  the `structured_output` field.
- **C.** Run with `--output-format json` and have the poster parse the `result` field instead
  of the raw output.
- **D.** Run with `--output-format stream-json` and have the poster rebuild each finding from
  the newline-delimited events.

**Answer:** B

**Evidence:** "uses regular expressions to pull ... out of the text" and "one run in ten posts
nothing" because the wording varied: the poster depends on free text, which has no
guaranteed shape.

**Why it wins:** pairing `--output-format json` with `--json-schema` makes Claude produce
output that conforms to the schema, delivered in the `structured_output` field. The poster
walks a typed array of findings and addresses each one to its file and line.

**Why the others fail:**
- **A:** a prompt instruction is probabilistic; preamble or a changed shape can still slip
  through, which is the failure the team already has.
- **C:** `--output-format json` alone wraps the run in metadata (session ID, cost), but the
  `result` field is still Claude's free text, so the regular expressions still have to guess.
- **D:** `stream-json` changes how the output is delivered, as events, not what shape the
  findings take; the poster would still be parsing prose.

**Note:** on one measured CLI build, a schema the CLI could not use degraded silently to prose
with `structured_output` set to null and exit code 0, so the CI step should check the field is
present before posting.

**Learn more:** https://code.claude.com/docs/en/headless

---

## Q-4.1 Design prompts with explicit criteria to improve precision and reduce false positives

**Meta:** Domain 4, Prompt engineering and structured output | Scenario: Claude Code for
Continuous Integration | Type: single choice

A pull request review step in your CI pipeline runs Claude Code with this instruction: "Review
the diff for problems. Be conservative and only report findings you are highly confident
about." The findings are well formatted, each with a location and a suggested fix. Developers
still dismiss most of them: they flag variable names that follow the repository's own naming
convention, early returns the reviewer would restructure, and the wording of log messages.
Meanwhile, a SQL query built by string concatenation was reported in one pull request and not
in an identical change a week later.

What is the most effective change?

- **A.** Have each finding carry a confidence score from 0 to 1, and drop findings below 0.8 in
  the pipeline before they are posted.
- **B.** Add three few-shot examples of findings formatted with location, issue, severity and
  suggested fix.
- **C.** Replace the instruction with explicit criteria: report correctness bugs and security
  issues such as injection or missing authorisation checks; do not report naming that follows
  local conventions, refactoring preferences or log message wording.
- **D.** Post-process the findings and remove any whose text contains "naming", "style" or
  "readability".

**Answer:** C

**Evidence:** "Be conservative" and "highly confident" are dispositions, not boundaries. The
noise falls in categories the team never wants (local conventions, preferences, wording), and
the injection reported once and missed once shows the boundary moving between runs. "Well
formatted" rules out a format problem.

**Why it wins:** a categorical criterion is a test with one answer per finding, so the model
applies it the same way each run. The report list fixes the missed injection; the do-not-report
list names the acceptable patterns that were arriving as false positives.

**Why the others fail:**
- **A:** confidence-based filtering is the same vague instruction wearing a number. The prompt
  already asks for high confidence and the noise comes through, because the score comes from
  the same process that is misjudging what counts.
- **B:** examples fix how findings are rendered; the findings are already well formatted. The
  defect is what counts as a finding, and examples do not supply the missing definition.
- **D:** a keyword filter on the output treats a symptom. It misses the early-return and log
  wording findings that use none of those words, and does nothing for the injection that the
  review sometimes misses.

**Note:** confidence is not banned outright. As a label a human reads inside each finding, or
as an input to routing calibrated on labelled data, it is correct (task 4.6). It fails here
because it replaces the criteria.

**Learn more:** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview

---

## Q-4.2 Apply few-shot prompting to improve output consistency and quality

**Meta:** Domain 4, Prompt engineering and structured output | Scenario: Multi-Agent Research
System | Type: single choice

In your multi-agent research system, the document analysis subagent extracts `sample_size` and
`study_design` from each paper into a schema where both fields are nullable. Its prompt explains
in detail what counts as a sample size and tells it to read the Methods section. Papers with a
labelled Methods section extract correctly. Short reports and preprints that state the number
only inside a narrative paragraph, such as "we recruited 212 nurses across four hospitals",
come back with `sample_size: null`, although the value is in the text. Some papers, such as
commentaries, genuinely report no sample size.

What should you do?

- **A.** Add a few examples to the prompt showing correct extraction from both layouts: a value
  under a Methods heading and a value stated inside a narrative paragraph, each with the
  extracted record.
- **B.** Extend the instructions with every heading a sample size may appear under, such as
  Participants, Study population and Materials.
- **C.** Make `sample_size` a required integer, so the subagent must find a value in every
  paper.
- **D.** Split each paper and send the subagent only its Methods section, so the number is not
  lost in a long document.

**Answer:** A

**Evidence:** "explains in detail" means detailed instructions are already there; the misses
happen only where the value sits "inside a narrative paragraph" with no heading; and "genuinely
report no sample size" means `null` must stay available.

**Why it wins:** this is extraction from varied document structures, where a value that is
present comes back empty because the model does not recognise it in an unfamiliar layout. An
example per layout shows the correct extraction from each, so the subagent learns where to look
rather than which heading to match, and generalises to new papers.

**Why the others fail:**
- **B:** more prose aimed at headings; the failing papers have no heading to match, so the list
  never fires.
- **C:** removes the correct answer for commentaries. A required field with no value in the
  document pressures the model to invent one.
- **D:** pre-filtering the input to the Methods section deletes the very paragraphs that hold
  the number in the failing papers, and those papers have no Methods section to send.

**Learn more:** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview

---

## Q-4.3 Structured output with tool use and JSON schemas

**Meta:** Domain 4, Prompt engineering and structured output | Scenario: Structured Data
Extraction | Type: single choice

You extract supplier invoices with a forced `extract_invoice` tool whose JSON schema marks
every field as a required string. About one invoice in twenty has no purchase order number
printed on it. For those, the extraction returns plausible-looking purchase order numbers
that appear nowhere in the document.

What is the most effective fix?

- **A.** Add to the prompt: "Never invent values. Only extract what is printed on the invoice."
- **B.** Change `tool_choice` to `"auto"`, so Claude can answer in text when a field is missing.
- **C.** Validate each purchase order number and, when it is not found in the document, retry
  the extraction with the error message.
- **D.** Make `purchase_order_number` nullable and say in its description that `null` is the
  correct value when no number is printed.

**Answer:** D

**Evidence:** "required string" plus "has no purchase order number printed": the schema
demands a value the document does not have, so the model supplies one.

**Why it wins:** fabrication here is a schema-design defect. A nullable field with a clear
description gives the model a correct way to say "not present".

**Why the others fail:**
- **A:** asks the model to resist the schema with a sentence; weaker than removing the
  pressure to invent.
- **B:** gives up the guarantee of structured output; the model may return text instead of
  calling the tool.
- **C:** a retry cannot find information that is not in the document; it will produce another
  invented number or fail again.

**Learn more:** https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview

---

## Q-4.4 Implement validation, retry, and feedback loops for extraction quality

**Meta:** Domain 4, Prompt engineering and structured output | Scenario: Structured Data
Extraction | Type: choose two

Your pipeline extracts vehicle repair estimates for an insurer with a forced tool call, then
validates each record in code. A record that fails validation is retried once, with the
original estimate, the failed extraction and the specific validation error. Today's validation
log lists five failed records, each from a different estimate.

Which two failures is that retry most likely to fix?

- **A.** `policy_number` is missing. The estimate says "policy number as per covering letter",
  and the covering letter is not sent with the request.
- **B.** `estimate_date` came back as "14 March 2026", but the validator requires ISO 8601.
- **C.** `stated_total` is £1,240 while the extracted parts and labour add up to £1,180. A claims
  handler checked the paper estimate: its own printed lines add up to £1,180.
- **D.** The garage's name was placed in `policy_holder` and the policy holder's name in
  `garage_name`. Both names appear, clearly labelled, in the estimate header.
- **E.** `vat_number` is `null`. The field is nullable, the validator treats `null` as an error,
  and this garage's estimate shows no VAT number.

**Answer:** B and D

**Evidence:** the date and both names are in the estimate, so the correct values can be derived
from what the model already has. The policy number lives in a document that was not sent, the
printed total contradicts the estimate's own lines, and the VAT number is not on the estimate
at all.

**Why it wins:**
- **B:** a format error. The error message names the field and the required format, and a second
  look at the same document can produce it.
- **D:** a structural error, a value placed in the wrong field. Both values are present and
  labelled, so the retry with the error named can move them.

**Why the others fail:**
- **A:** the information is external to the request. A retry cannot find it, and a prompt that
  says a blank is unacceptable invites an invented number. Fix the pipeline input or route the
  record to a human.
- **C:** not an extraction error but a conflict in the source. Retrying asks the model to make
  the contradiction disappear by silently picking a side. Extract `stated_total` alongside
  `calculated_total`, set `conflict_detected`, and route it to a human.
- **E:** `null` in a nullable field for a value the document lacks is correct output. The defect
  is the validator; retrying pressures the model to fabricate a VAT number.

**Learn more:** https://platform.claude.com/docs/en/build-with-claude/structured-outputs

---

## Q-4.5 Design efficient batch processing strategies

**Meta:** Domain 4, Prompt engineering and structured output | Scenario: Structured Data
Extraction | Type: single choice

Each night you submit 2,000 supplier contracts to the Message Batches API, one forced tool call
extraction request per contract, with the contract ID as `custom_id`. This morning's results:
1,960 succeeded and have already been validated and written downstream by `custom_id`. 28
errored with `invalid_request` because they exceeded the context limit; they are the longest
contracts, with their appendices attached. 12 expired without being processed inside the
24-hour window.

What should you do next?

- **A.** Resubmit the whole batch of 2,000 with a shorter prompt, so every contract is processed
  under the same prompt.
- **B.** Resubmit all 40 failed contracts unchanged in the next batch, identified by their
  `custom_id`.
- **C.** Send the 28 long contracts without appendices and give the extraction request a tool
  that fetches an appendix, so Claude can request each one mid-request; resubmit the 12 expired
  contracts unchanged.
- **D.** Resubmit only the 40 failures, identified by `custom_id`: split the 28 oversized
  contracts into chunks first, and send the 12 expired contracts unchanged.

**Answer:** D

**Evidence:** "already been validated and written downstream" rules out re-running the
successes. "exceeded the context limit" is a property of the request, so those items need a
change. "expired without being processed" is not a property of the request, so those need none.

**Why it wins:** each batch item succeeds or fails on its own, and `custom_id` identifies the
failures. Resubmit only those, with the modification each error implies: chunk the oversized
documents, and resend the expired ones as they were.

**Why the others fail:**
- **A:** pays again for 1,960 records that are done and may change records already committed
  downstream. A shorter prompt also does not shrink a contract with its appendices.
- **B:** right set, wrong treatment for 28 of them. An `invalid_request` resubmitted unchanged
  returns the same error after another window.
- **C:** a batch request cannot run multi-turn tool calling: no code runs between turns to
  execute the tool and return its result, so the appendix never arrives.

**Learn more:** https://platform.claude.com/docs/en/build-with-claude/batch-processing

---

## Q-4.6 Design multi-instance and multi-pass review architectures

**Meta:** Domain 4, Prompt engineering and structured output | Scenario: Claude Code for
Continuous Integration | Type: single choice

Your CI pipeline uses `claude -p` to write unit tests for changed modules. A second step then
resumes that same session by its session ID and asks: "Review the tests you just wrote for
mistakes." The review almost never finds anything. Human reviewers, though, keep finding tests
that assert the module's current buggy behaviour as correct. In the review transcript, Claude
re-reads those assertions, refers back to its earlier reasoning that the behaviour was
intended, and approves them. It describes the module's documented behaviour accurately.

How should you change the review step?

- **A.** Run the review as a separate `claude -p` invocation that receives only the diff, the
  generated tests and the review criteria, not the generation session.
- **B.** Fork the generation session and run the review in the fork, so the review cannot alter
  the original session's history.
- **C.** Keep resuming the generation session, but enable extended thinking for the review step
  so Claude reasons longer about each assertion.
- **D.** Add the module's full API documentation and existing test suite to the review step's
  context.

**Answer:** A

**Evidence:** "resumes that same session" and "refers back to its earlier reasoning": the
reviewer is reading the justification it wrote while generating. "Describes the module's
documented behaviour accurately" rules out a knowledge gap.

**Why it wins:** a model that keeps its generation reasoning in context is less likely to
question its own decisions. A separate instance that never saw that reasoning reviews the
artefact on its merits, like a human peer reviewer, and catches what the author rationalised.

**Why the others fail:**
- **B:** a fork starts from the generation session's history, so the reviewer still sees the
  reasoning that approved the assertions. Isolation from the generator's reasoning, not
  protection of the original session, is what the review needs.
- **C:** more deliberation inside the same context. The bias is in what the model can see, not
  in how long it thinks.
- **D:** treats the failure as missing information; the transcript shows the reviewer already
  knows the documented behaviour and approves the assertions anyway.

**Learn more:** https://code.claude.com/docs/en/headless

---

## Q-5.1 Conversation context across long interactions

**Meta:** Domain 5, Context management and reliability | Scenario: Customer Support Resolution
Agent | Type: single choice

Your support agent, built with the Claude Agent SDK, summarises older turns once the history
passes a token threshold. In one long session a customer raised two issues: order ORD-4471
arrived damaged (£64.00, they want a replacement) and order ORD-4502 was charged twice
(£212.50, they want the duplicate refunded). After a summarisation pass, the history reads
"customer has a damaged item and a billing problem across two orders". Twenty turns later,
without the customer referring back to anything, the agent offers a £64.00 refund for the
duplicate charge.

What is the most effective fix?

- **A.** Revise the summarisation prompt so it keeps every order number, amount and requested
  outcome verbatim.
- **B.** Raise the summarisation threshold so the first summary happens much later in the
  conversation.
- **C.** Keep one structured record per issue (order ID, amount, requested outcome, status)
  outside the summarised history, update it from tool results and customer statements, and
  include it in every prompt.
- **D.** Store the full transcript externally and retrieve the earlier turns whenever the
  customer refers back to something they said.

**Answer:** C

**Evidence:** "a damaged item and a billing problem across two orders" is a summary that has
blurred the amounts and outcomes, and the £64.00 from one issue landing on the other is two
issues competing for one set of facts. "Without the customer referring back" shows the agent
needs these facts on every turn, not only when prompted.

**Why it wins:** transactional facts kept in a structured block the summariser never touches
cannot be blurred by it. One record per issue stops amounts and statuses crossing between
issues, and the block is short enough to resend on every turn.

**Why the others fail:**
- **A:** an instruction to the summariser is probabilistic, and summarisation inherently loses
  precise detail; the block is structural.
- **B:** delays the loss by some turns; the first summary still blurs the same facts.
- **D:** retrieval depends on a reference being detected, and here there was none. A fact the
  agent needs on every turn should not depend on a heuristic firing.

**Learn more:** https://code.claude.com/docs/en/agent-sdk/sessions

---

## Q-5.2 Escalation and ambiguity resolution

**Meta:** Domain 5, Context management and reliability | Scenario: Customer Support Resolution
Agent | Type: single choice

A customer writes: "My parcel is three days late and I want to speak to a person, not a bot."
The delay is a routine carrier issue that your support agent could resolve on its own by
issuing a delivery credit.

What should the agent do?

- **A.** Acknowledge the frustration, offer the delivery credit, and escalate only if the
  customer asks for a person again.
- **B.** Escalate to a human now with a structured handoff, without investigating first.
- **C.** Look up the order first, so the human receives complete information, then escalate.
- **D.** Escalate only if a sentiment check scores the message as highly negative.

**Answer:** B

**Evidence:** "I want to speak to a person": an explicit request for a human, which is a
trigger on its own, whatever the complexity of the issue.

**Why it wins:** an explicit request for a human is honoured immediately. The handoff carries
what the agent already has, so the human does not start from nothing.

**Why the others fail:**
- **A:** the right move for frustration without a request; here the customer has already
  asked, so offering to resolve first ignores them.
- **C:** "investigate first" after an explicit request is the polite-sounding wrong answer.
- **D:** sentiment is a poor proxy for whether to escalate, and the request alone decides it.

**Learn more:** https://code.claude.com/docs/en/agent-sdk/overview

---

## Q-5.3 Error propagation across multi-agent systems

**Meta:** Domain 5, Context management and reliability | Scenario: Multi-Agent Research System
| Type: single choice

In your research system, the document-analysis subagent receives 40 regulatory filings per run.
Logs show two kinds of failure. The filing archive's API sometimes returns rate-limit errors
that succeed when retried a few seconds later. And a few filings are scanned images that the
subagent's text parser cannot read at all, however often it tries. Today, any failure makes the
subagent stop and return "analysis failed" for the whole batch, and the coordinator restarts
the run from the beginning.

How should the subagent handle failures?

- **A.** Retry rate-limit errors locally with exponential backoff and a small retry limit; for
  the scanned filings, finish the rest of the batch and return a structured error with the
  failure type, the filings attempted, the completed results and alternatives such as a
  different parsing method.
- **B.** Retry every failed filing up to three times with exponential backoff, then return
  "analysis unavailable" for any filing that still fails, so the coordinator knows which ones
  are missing.
- **C.** Skip any filing that fails and return the completed analyses with a success status,
  so the coordinator can move straight on to synthesis without a restart.
- **D.** Send every failure to the coordinator immediately as a structured error with the raw
  exception, so the coordinator decides each retry with its broader view of the run.

**Answer:** A

**Evidence:** "succeed when retried a few seconds later" marks the rate-limit errors as
transient; "cannot read at all, however often it tries" marks the scanned filings as not
transient. "Stop and return 'analysis failed' for the whole batch" combines a generic status
with terminating everything on a single failure.

**Why it wins:** recovery belongs at the lowest layer that can resolve the error, so the
subagent retries what a retry can fix, with a bound. What it cannot fix travels up with
enough context (failure type, what was attempted, partial results, alternatives) for the
coordinator to choose between retrying differently, using the partial results or annotating
the gap.

**Why the others fail:**
- **B:** retrying the scanned filings burns time on something that cannot change, and
  "analysis unavailable" is a generic status that hides why it failed and what could work.
- **C:** silent suppression: failures reported as success leave the coordinator unable to
  recover, and the report will imply coverage it does not have.
- **D:** moves routine recovery up to the coordinator, the opposite of local recovery first;
  the subagent already knows a rate limit is worth retrying.

**Learn more:** https://code.claude.com/docs/en/agent-sdk/subagents

---

## Q-5.4 Context in large codebase exploration

**Meta:** Domain 5, Context management and reliability | Scenario: Code Generation with Claude
Code | Type: single choice

A developer is using one long Claude Code session to understand a legacy billing module before
a refactor. Early on, Claude Code found that `InvoiceBuilder` in `src/billing/builder.py` is
called from exactly three places and that a `tax_region` column was added by migration 112.
Two hours and many file reads later, its answers describe "the usual builder pattern", list
callers that contradict its earlier findings, and no longer mention the migration. The
investigation will continue over the next several days.

What should the developer do?

- **A.** Switch to a model with a larger context window, so the earlier file reads stay
  available for the rest of the investigation.
- **B.** Run `/compact` to free up the context window, then keep asking questions in the same
  session.
- **C.** Add a line to `CLAUDE.md`: "Always refer to the specific classes found earlier in the
  session, never to typical patterns."
- **D.** Have Claude Code record key findings (class names, file paths, call sites, migrations)
  in a scratchpad file as it discovers them, and re-read that file before answering each
  later question.

**Answer:** D

**Evidence:** "describe 'the usual builder pattern'" and answers that "contradict its earlier
findings" are the named symptoms of context degradation in an extended session: typical
patterns replacing the specific classes discovered earlier. "Over the next several days" means
the findings must also survive session boundaries.

**Why it wins:** a scratchpad file puts the specific facts on disk, where neither a filling
window, compaction nor a new session can lose them. Writing it is half the technique;
re-reading it before each answer is what counteracts the degradation.

**Why the others fail:**
- **A:** a bigger window does not fix attention quality; the session is degrading, not
  overflowing.
- **B:** `/compact` relieves a full window, but a bare compaction is lossy: it summarises the
  very names and numbers that are already slipping, and nothing tells it what to keep.
- **C:** an instruction cannot restore facts that are no longer reliably in context, and
  investigation findings are task state, not a standing rule for every session.

**Learn more:** https://code.claude.com/docs/en/common-workflows

---

## Q-5.5 Human review workflows and confidence calibration

**Meta:** Domain 5, Context management and reliability | Scenario: Structured Data Extraction |
Type: choose two

Your extraction system processes supplier invoices, purchase orders and delivery notes. The
model outputs a confidence score for each field, and the review threshold of 0.9 was calibrated
on a labelled validation set. Today every record is reviewed by a person. The team proposes to
stop reviewing all fields scored above 0.9, citing 98.4% field accuracy across last quarter's
reviewed records. Delivery notes are 4% of volume and come in dozens of carrier layouts, and new
suppliers are onboarded every month.

Which two practices should the team adopt as it reduces human review?

- **A.** Have the model also rate each whole record from 1 to 10, and approve records rated 9 or
  above without review.
- **B.** Measure accuracy separately by document type and by field on labelled data, and remove
  review only for the segments whose own accuracy meets the target.
- **C.** Send a simple random 1% of all records to reviewers each week to track the overall
  error rate.
- **D.** Have reviewers check the records below the threshold more thoroughly, since that is
  where most errors will be.
- **E.** Keep sending a sample of the high-confidence extractions to review, stratified by
  document type and field, to measure their error rate and spot new error patterns.

**Answer:** B and E

**Evidence:** "98.4% field accuracy across last quarter's reviewed records" is an aggregate,
and "delivery notes are 4% of volume" is a segment small enough to hide inside it. "New
suppliers are onboarded every month" means layouts the calibration set never saw will keep
arriving.

**Why it wins:**
- **B:** an aggregate can mask a document type or field that fails badly; automation has to be
  justified segment by segment before review is reduced.
- **E:** once review stops, the high-confidence stream is the part nobody reads. A stratified
  sample keeps measuring its error rate, includes the rare segments, and surfaces confident
  errors from layouts the calibration never covered.

**Why the others fail:**
- **A:** a self-rated, record-level score that was never calibrated, used as an autonomous
  gate, is the form of confidence the exam rejects; it also discards the calibrated per-field
  scores.
- **C:** a simple random sample of all records contains almost none of a 4% segment, and much of
  it falls in records humans already review.
- **D:** auditing the low-confidence queue measures what people already read; the blind spot is
  the automated stream.

**Note:** the exam rejects a raw self-rated confidence score used as an escalation gate, yet
prescribes per-field scores calibrated on labelled data and audited by sampling. The
qualifiers are what items test.

**Learn more:** https://platform.claude.com/docs/en/build-with-claude/structured-outputs

---

## Q-5.6 Provenance and uncertainty in multi-source synthesis

**Meta:** Domain 5, Context management and reliability | Scenario: Multi-Agent Research System
| Type: single choice

Your research system's search subagents return their findings as short prose summaries, such as
"A national survey found 22% of small firms use AI tools" and "An industry study puts small-firm
AI adoption at 31%". The synthesis subagent's report lists these under "Contradictory evidence".
A reviewer opens both sources and finds that the first survey collected its data in 2022 and
the second in 2025, so the figures are consistent with growth rather than a contradiction.

What is the most effective fix?

- **A.** Instruct the synthesis subagent to work out when each figure was collected from the
  wording of the findings before it compares them.
- **B.** Require each search subagent to return structured findings with the claim, an evidence
  excerpt, the source name or URL and the publication or data collection date, and have
  synthesis preserve them.
- **C.** Have the synthesis subagent report the average of conflicting figures, citing both
  sources, so the report gives readers one number.
- **D.** Have the synthesis subagent keep the figure from the more authoritative source and
  mention the other in a footnote.

**Answer:** B

**Evidence:** "short prose summaries" with no dates, and figures collected in "2022" and "2025"
that were reported as contradictory: a temporal difference was misread as a conflict because
the date never reached the synthesis step.

**Why it wins:** dates and sources have to travel as data beside each claim from the first
agent onward. With collection dates in the structured output, synthesis can read 22% then 31%
as a change over time, and every claim keeps its source through the merge.

**Why the others fail:**
- **A:** the date is a required field, not an inference. By synthesis time only the prose is
  left, and these summaries contain no date to find.
- **C:** an average is a figure no source published, so it cannot be attributed, and here it
  hides the growth that was the actual finding.
- **D:** arbitrarily selecting one value discards credible evidence; real conflicts are
  annotated with attribution, not resolved by picking.

**Learn more:** https://code.claude.com/docs/en/agent-sdk/subagents
