# Discovery doc: campaign request intake

This is the kind of one-pager a forward-deployed engineer would write after a
discovery call with an enterprise marketing team, before writing any code. It
states the problem in the customer's language, then works backward to a
system design. The build in this repo is the "prototype" output of that
process.

## The problem, as a stakeholder would describe it

> "Every time we want to run a campaign, someone on the marketing team sends
> a Slack message or an email that's basically a paragraph of intent — 'we
> need a push for the fall promo, targeting existing customers, launch by
> next Friday.' Then an ops person has to manually turn that into a brief
> doc, break it into tasks, assign owners, and get it all into the project
> tracker before anyone can actually start work. That translation step takes
> a day or two and it's the same shape of work every time, just different
> details."

Stripped of specifics, the pattern is: **unstructured intent in, structured
execution-ready plan out, written into whatever system the team already
works in.** That's a good candidate for automation precisely because the
translation is repetitive and well-scoped, but the input is genuinely
ambiguous — there's no form, no dropdown, just a sentence a person wrote in a
hurry.

## Why this isn't a simple form

The naive fix is "give them a structured intake form." Two things make that
the wrong answer in practice, and they're both worth stating explicitly
because they're the actual argument for an LLM in this pipeline rather than
plain business logic:

1. **The ambiguity is the point.** Stakeholders don't reliably know the full
   shape of what they need up front — they know the objective and maybe a
   date. Forcing them to fill out "channels," "deliverables," and "task
   owners" up front just relocates the translation work onto the person
   least equipped to do it, or gets skipped/half-filled under deadline
   pressure.
2. **The output has to match how the org actually works**, not a generic
   template — different teams use different channel names, different task
   owner titles, different tools. A rules engine (`if "social" in text then
   channel = "Paid Social"`) breaks the moment someone phrases things
   slightly differently, and multiplies its own maintenance burden per
   customer, which is exactly the "scalable onboarding" problem an FDE has
   to solve for repeatedly across enterprise accounts.

## System design

Two consequences follow directly from that framing, and they're the two
architectural decisions in this repo:

**Decision 1 — split planning from execution.** Planning (turning ambiguous
text into a structured plan) and execution (writing that plan into a real
system) are different failure modes and different trust levels. Planning
should be flexible and can be iterated on / regenerated cheaply. Execution
writes real records into a real workspace and should be deterministic,
auditable, and driven by explicit tool calls rather than free-form text
generation — hence the two-phase design: one structured-output call for the
plan, then a constrained tool-calling loop (exactly two tools, `create_campaign_brief`
and `create_task_list`) for execution. The model can reason about *when* to
act, never about *what* the API call looks like — that's fixed in code.

**Decision 2 — never let the orchestration logic know which workflow tool
it's talking to.** The customer's tool is a fact learned during discovery,
not an assumption baked into the pipeline. `WorkflowToolAdapter` is the
seam: the agent loop calls `create_brief()` / `create_tasks()` on an
interface, and which concrete class answers that call (Notion here; Airtable,
Asana, or a customer's in-house tool in a real deployment) is a
configuration decision, not a rewrite. This is the part of the system
designed for the second and third customer, not just the first.

## What "done" looks like for the prototype

- A marketer can submit one sentence of real intent and, without further
  input, get a campaign brief and a set of assigned, dated tasks live in the
  team's actual workflow tool.
- Every step the agent takes is visible and attributable — not a black box —
  because in an enterprise context "the AI did something to our workspace"
  has to be inspectable after the fact.
- Swapping the destination system is a new adapter class, not a rewrite of
  the planning or agent logic.

## What a real second iteration would add

This prototype intentionally stops before the parts that would come from
actually sitting with a customer:

- **Human-in-the-loop approval** before the agent writes anything — the
  natural next step once a real customer sees the agent act autonomously and
  (reasonably) wants a review gate first. The system already separates plan
  from execution, so adding an approval step between them is additive, not a
  redesign.
- **Per-customer configuration** for task owner roles, channel vocabulary,
  and due-date conventions, learned during onboarding rather than hardcoded
  in the prompt.
- **A second adapter** (their actual tool, not Notion) built from the same
  interface, to prove the abstraction holds under a real second case rather
  than just in theory.
