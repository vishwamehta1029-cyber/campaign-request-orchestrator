"""Fake-but-realistic adapter so the whole app runs with zero external
accounts. This is what powers the app before you drop in real API keys,
and it's also what a unit test would use as a fake.
"""
from typing import List, Dict, Any
import time
import uuid

from ..models import CampaignPlan
from .base import WorkflowToolAdapter


class MockNotionAdapter(WorkflowToolAdapter):
    name = "notion (mock)"

    def health_check(self) -> Dict[str, Any]:
        return {"connected": True, "detail": "Running in MOCK MODE — add NOTION_API_KEY to go live"}

    def create_brief(self, plan: CampaignPlan) -> Dict[str, Any]:
        time.sleep(0.4)  # simulate network latency for a believable demo pace
        fake_id = uuid.uuid4().hex
        slug = plan.campaign_name.lower().replace(" ", "-")[:40]
        return {"id": fake_id, "url": f"https://notion.so/mock-workspace/{slug}-{fake_id[:8]}"}

    def create_tasks(self, plan: CampaignPlan, brief_id: str) -> List[Dict[str, Any]]:
        created = []
        for task in plan.tasks:
            time.sleep(0.15)
            tid = uuid.uuid4().hex
            slug = task.title.lower().replace(" ", "-")[:30]
            created.append({"id": tid, "url": f"https://notion.so/mock-workspace/task-{slug}-{tid[:8]}", "title": task.title})
        return created


def get_adapter() -> WorkflowToolAdapter:
    from ..config import settings

    if settings.notion_live:
        from .notion_adapter import NotionAdapter

        return NotionAdapter()
    return MockNotionAdapter()
