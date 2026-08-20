from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models import CampaignRequest, NewRequestBody
from . import store, agent, ratelimit
from .integrations.mock_adapter import get_adapter

app = FastAPI(title="Campaign Request Orchestrator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/status")
def status():
    adapter = get_adapter()
    return {
        "agent_live": settings.agent_live,
        "agent_model": settings.openai_model if settings.agent_live else "mock-planner",
        "workflow_tool": adapter.name,
        "workflow_tool_health": adapter.health_check(),
        "rate_limit_per_hour": settings.max_requests_per_ip_per_hour if settings.agent_live else None,
    }


@app.post("/api/requests", status_code=202)
def create_request(body: NewRequestBody, request: Request, background_tasks: BackgroundTasks):
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > settings.max_request_text_chars:
        raise HTTPException(400, f"Keep requests under {settings.max_request_text_chars} characters.")

    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown").split(",")[0].strip()
    ratelimit.check_and_record(client_ip, live=settings.agent_live)

    req = CampaignRequest(raw_text=text)
    store.save(req)

    adapter = get_adapter()
    background_tasks.add_task(agent.run_pipeline, req.id, adapter)
    return req


@app.get("/api/requests")
def list_requests():
    return store.list_all()


@app.get("/api/requests/{request_id}")
def get_request(request_id: str):
    req = store.get(request_id)
    if req is None:
        raise HTTPException(404, "not found")
    return req
