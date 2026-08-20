from typing import List, Optional, Literal
from pydantic import BaseModel, Field
import uuid
import time

Stage = Literal[
    "received",
    "planning",
    "drafting_brief",
    "creating_tasks",
    "syncing_notion",
    "complete",
    "error",
]

TraceType = Literal["reasoning", "tool_call", "tool_result", "system", "error"]


class TraceEntry(BaseModel):
    ts: float = Field(default_factory=time.time)
    type: TraceType
    message: str
    detail: Optional[dict] = None


class CampaignTask(BaseModel):
    title: str
    owner_role: str
    due_date: Optional[str] = None


class CampaignPlan(BaseModel):
    campaign_name: str
    objective: str
    audience: str
    channels: List[str]
    key_dates: str
    deliverables: List[str]
    tasks: List[CampaignTask]


class NewRequestBody(BaseModel):
    text: str


class CampaignRequest(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    raw_text: str
    stage: Stage = "received"
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    plan: Optional[CampaignPlan] = None
    trace: List[TraceEntry] = Field(default_factory=list)
    notion_brief_url: Optional[str] = None
    notion_task_urls: List[str] = Field(default_factory=list)
    error: Optional[str] = None
