"""The agent: turns one ambiguous sentence from a marketer into a
structured campaign plan, then actually executes it against a real
workflow tool via tool-calling.

Two phases, mirroring how Gradial's platform is described in the job
posting (discovery -> execution):

  Phase 1 - PLAN   : one structured-output LLM call turns free text into
                      a CampaignPlan (audience, channels, tasks, etc).
  Phase 2 - EXECUTE : a genuine OpenAI tool-calling loop where the model
                      decides when to call create_campaign_brief and
                      create_task_list. Our Python code executes those
                      calls for real against the WorkflowToolAdapter and
                      feeds the results back, until the model is done.

If OPENAI_API_KEY is not set, both phases fall back to a deterministic
heuristic "mock agent" so the whole product is demoable with zero keys.
"""
import json
import re
import time
from typing import List

from .config import settings
from .models import CampaignRequest, CampaignPlan, CampaignTask, TraceEntry
from .integrations.base import WorkflowToolAdapter
from . import store

PLAN_SCHEMA = {
    "name": "campaign_plan",
    "schema": {
        "type": "object",
        "properties": {
            "campaign_name": {"type": "string"},
            "objective": {"type": "string"},
            "audience": {"type": "string"},
            "channels": {"type": "array", "items": {"type": "string"}},
            "key_dates": {"type": "string"},
            "deliverables": {"type": "array", "items": {"type": "string"}},
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "owner_role": {"type": "string"},
                        "due_date": {"type": "string"},
                    },
                    "required": ["title", "owner_role", "due_date"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["campaign_name", "objective", "audience", "channels", "key_dates", "deliverables", "tasks"],
        "additionalProperties": False,
    },
    "strict": True,
}

PLANNER_SYSTEM_PROMPT = """You are a marketing operations planning agent inside an enterprise \
martech orchestration platform. A stakeholder will describe a campaign request in loose, \
ambiguous, real-world language. Turn it into a concrete, execution-ready campaign plan.

Rules:
- Infer sensible specifics when the request is vague (e.g. pick 2-4 realistic channels, a \
  realistic timeline, and 3-6 concrete tasks with owner roles like 'Copywriter', 'Paid Media \
  Manager', 'Designer', 'Marketing Ops') rather than asking a clarifying question.
- Tasks must be concrete and actionable, not vague restatements of the objective.
- Keep the objective and audience to one crisp sentence each.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_campaign_brief",
            "description": "Create the campaign brief record in the customer's workflow tool. Call this first.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task_list",
            "description": "Create the task records in the customer's workflow tool, linked to the brief. Call this after the brief exists.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
]

EXECUTOR_SYSTEM_PROMPT = """You are an execution agent. You have a finalized campaign plan and \
access to two tools that write into the customer's workflow tool. Call create_campaign_brief \
exactly once, then call create_task_list exactly once, then reply with a one or two sentence \
confirmation summary for the marketer who submitted the request. Do not call a tool more than once.
"""


def _trace(req: CampaignRequest, type_: str, message: str, detail: dict = None):
    req.trace.append(TraceEntry(type=type_, message=message, detail=detail))
    req.updated_at = time.time()
    store.save(req)


def run_pipeline(request_id: str, adapter: WorkflowToolAdapter):
    req = store.get(request_id)
    if req is None:
        return
    try:
        _trace(req, "system", "Request received by orchestrator.")

        req.stage = "planning"
        _trace(req, "reasoning", "Parsing free-text request into a structured campaign plan…")
        plan = _plan(req.raw_text, req)
        req.plan = plan
        _trace(req, "reasoning", f"Plan drafted: '{plan.campaign_name}' across {len(plan.channels)} channel(s), {len(plan.tasks)} task(s).")

        req.stage = "drafting_brief"
        _trace(req, "system", "Handing plan to the execution agent.")
        _execute(req, plan, adapter)

        req.stage = "syncing_notion"
        health = adapter.health_check()
        _trace(req, "tool_result", f"Verified sync with {adapter.name}.", health)

        req.stage = "complete"
        _trace(req, "system", "Pipeline complete.")
    except Exception as e:  # noqa: BLE001 - demo app: surface any failure to the UI
        req.stage = "error"
        req.error = str(e)
        _trace(req, "error", f"Pipeline failed: {e}")
    finally:
        store.save(req)


# ---------------------------------------------------------------------------
# Phase 1: planning
# ---------------------------------------------------------------------------

def _plan(text: str, req: CampaignRequest) -> CampaignPlan:
    if settings.agent_live:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            response_format={"type": "json_schema", "json_schema": PLAN_SCHEMA},
        )
        data = json.loads(resp.choices[0].message.content)
        return CampaignPlan(**data)

    _trace(req, "system", "OPENAI_API_KEY not set — using deterministic mock planner.")
    return _mock_plan(text)


_STOPWORDS = {
    "we", "need", "a", "an", "the", "for", "our", "us", "to", "and", "with",
    "of", "in", "on", "by", "please", "can", "you", "i", "want", "would",
    "like", "get", "some", "that", "this", "have", "has", "is", "are", "be",
}


def _guess_campaign_name(text: str) -> str:
    """Pull a plausible campaign name out of a free-text request, e.g.
    'We need a paid social and email campaign for our fall promo...' -> 'Fall Promo'.
    """
    m = re.search(r"for (?:our |the |a )?([a-z0-9 '\-]{3,40}?)(?:,|\.|;| targeting| launching| by |$)", text, re.I)
    if m:
        candidate = m.group(1).strip()
        if candidate and candidate.lower() not in _STOPWORDS:
            return " ".join(w.capitalize() for w in candidate.split())

    words = [w for w in re.findall(r"[A-Za-z']+", text) if w.lower() not in _STOPWORDS]
    if words:
        return " ".join(w.capitalize() for w in words[:4])
    return "New Campaign"


def _mock_plan(text: str) -> CampaignPlan:
    """Cheap heuristic stand-in for the LLM so the app works with zero keys."""
    lowered = text.lower()

    channel_bank = {
        "social": "Paid Social", "paid": "Paid Search", "email": "Email", "seo": "SEO",
        "content": "Content Marketing", "influencer": "Influencer", "display": "Display Ads",
        "affiliate": "Affiliate",
    }
    channels = [v for k, v in channel_bank.items() if k in lowered]
    if not channels:
        channels = ["Email", "Paid Social"]

    date_match = re.search(r"by\s+([A-Za-z]+\s+\d{1,2}|\bnext\s+\w+\b|\d{1,2}/\d{1,2})", text, re.I)
    key_dates = f"Launch {date_match.group(1)}" if date_match else "Launch date TBD — recommend 3-week runway"

    name_guess = _guess_campaign_name(text)

    audience = "Existing customers" if "existing" in lowered or "customer" in lowered else "Target segment (inferred from request)"

    deliverables = [f"{c} creative package" for c in channels] + ["Campaign brief one-pager"]

    tasks: List[CampaignTask] = [
        CampaignTask(title=f"Draft {channels[0]} creative brief", owner_role="Copywriter", due_date="T-10 days"),
        CampaignTask(title="Design campaign assets", owner_role="Designer", due_date="T-7 days"),
        CampaignTask(title="Configure audience targeting", owner_role="Paid Media Manager", due_date="T-5 days"),
        CampaignTask(title="QA links, tracking, and UTM parameters", owner_role="Marketing Ops", due_date="T-2 days"),
        CampaignTask(title="Launch and monitor initial performance", owner_role="Campaign Manager", due_date="T-0"),
    ]

    return CampaignPlan(
        campaign_name=name_guess[:60] or "New Campaign",
        objective=f"Drive measurable engagement via {', '.join(channels).lower()} based on the stakeholder's request.",
        audience=audience,
        channels=channels,
        key_dates=key_dates,
        deliverables=deliverables,
        tasks=tasks,
    )


# ---------------------------------------------------------------------------
# Phase 2: execution (real tool-calling loop, or mock equivalent)
# ---------------------------------------------------------------------------

def _execute(req: CampaignRequest, plan: CampaignPlan, adapter: WorkflowToolAdapter):
    if settings.agent_live:
        _execute_live(req, plan, adapter)
    else:
        _execute_mock(req, plan, adapter)


def _execute_live(req: CampaignRequest, plan: CampaignPlan, adapter: WorkflowToolAdapter):
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    plan_json = plan.model_dump_json(indent=2)
    messages = [
        {"role": "system", "content": EXECUTOR_SYSTEM_PROMPT},
        {"role": "user", "content": f"Finalized plan:\n{plan_json}"},
    ]

    brief_result = None
    max_turns = 5
    for _ in range(max_turns):
        resp = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            tools=TOOLS,
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            _trace(req, "reasoning", msg.content or "Agent finished.")
            break

        for call in msg.tool_calls:
            fn = call.function.name
            _trace(req, "tool_call", f"Agent called `{fn}`", {"tool": fn})

            if fn == "create_campaign_brief":
                brief_result = adapter.create_brief(plan)
                req.notion_brief_url = brief_result["url"]
                result = brief_result
                _trace(req, "tool_result", f"Brief created in {adapter.name} → {brief_result['url']}", result)
                req.stage = "creating_tasks"
            elif fn == "create_task_list":
                brief_id = brief_result["id"] if brief_result else ""
                tasks_result = adapter.create_tasks(plan, brief_id)
                req.notion_task_urls = [t["url"] for t in tasks_result]
                result = {"tasks_created": len(tasks_result)}
                _trace(req, "tool_result", f"{len(tasks_result)} task(s) created in {adapter.name}", {"tasks": tasks_result})
            else:
                result = {"error": f"unknown tool {fn}"}

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result),
            })
        store.save(req)


def _execute_mock(req: CampaignRequest, plan: CampaignPlan, adapter: WorkflowToolAdapter):
    _trace(req, "reasoning", "Agent decides to record the brief before creating tasks (mock reasoning).")
    _trace(req, "tool_call", "Agent called `create_campaign_brief`", {"tool": "create_campaign_brief"})
    brief = adapter.create_brief(plan)
    req.notion_brief_url = brief["url"]
    _trace(req, "tool_result", f"Brief created in {adapter.name} → {brief['url']}", brief)

    req.stage = "creating_tasks"
    _trace(req, "tool_call", "Agent called `create_task_list`", {"tool": "create_task_list"})
    tasks = adapter.create_tasks(plan, brief["id"])
    req.notion_task_urls = [t["url"] for t in tasks]
    _trace(req, "tool_result", f"{len(tasks)} task(s) created in {adapter.name}", {"tasks": tasks})

    _trace(req, "reasoning", f"Done. '{plan.campaign_name}' is staged with {len(tasks)} task(s) ready for the team.")
