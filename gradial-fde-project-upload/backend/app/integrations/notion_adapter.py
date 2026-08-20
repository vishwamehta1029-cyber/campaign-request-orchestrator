"""Real Notion implementation of WorkflowToolAdapter.

Uses the raw Notion REST API via `requests` (no SDK dependency) so the
HTTP contract is fully visible -- useful to walk through in an interview.
Docs: https://developers.notion.com/reference/intro
"""
from typing import List, Dict, Any
import requests

from ..models import CampaignPlan
from ..config import settings
from .base import WorkflowToolAdapter

NOTION_VERSION = "2022-06-28"
API_BASE = "https://api.notion.com/v1"


class NotionAdapter(WorkflowToolAdapter):
    name = "notion"

    def __init__(self):
        self.api_key = settings.notion_api_key
        self.parent_page_id = settings.notion_parent_page_id
        self.tasks_db_id = settings.notion_tasks_database_id

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    def health_check(self) -> Dict[str, Any]:
        try:
            resp = requests.get(f"{API_BASE}/users/me", headers=self._headers(), timeout=8)
            if resp.status_code == 200:
                bot = resp.json()
                return {"connected": True, "detail": f"Authenticated as {bot.get('name', 'Notion integration')}"}
            return {"connected": False, "detail": f"Notion returned {resp.status_code}: {resp.text[:200]}"}
        except requests.RequestException as e:
            return {"connected": False, "detail": f"Network error: {e}"}

    def create_brief(self, plan: CampaignPlan) -> Dict[str, Any]:
        body = {
            "parent": {"page_id": self.parent_page_id},
            "properties": {
                "title": [{"text": {"content": plan.campaign_name}}],
            },
            "children": [
                _heading("Objective"),
                _paragraph(plan.objective),
                _heading("Audience"),
                _paragraph(plan.audience),
                _heading("Channels"),
                _paragraph(", ".join(plan.channels)),
                _heading("Key Dates"),
                _paragraph(plan.key_dates),
                _heading("Deliverables"),
                *[_bullet(d) for d in plan.deliverables],
            ],
        }
        resp = requests.post(f"{API_BASE}/pages", headers=self._headers(), json=body, timeout=15)
        resp.raise_for_status()
        page = resp.json()
        return {"id": page["id"], "url": page.get("url", "")}

    def create_tasks(self, plan: CampaignPlan, brief_id: str) -> List[Dict[str, Any]]:
        created = []
        for task in plan.tasks:
            body = {
                "parent": {"database_id": self.tasks_db_id},
                "properties": {
                    "Name": {"title": [{"text": {"content": task.title}}]},
                    "Owner": {"rich_text": [{"text": {"content": task.owner_role}}]},
                    "Due": {"rich_text": [{"text": {"content": task.due_date or "TBD"}}]},
                    "Campaign": {"rich_text": [{"text": {"content": brief_id}}]},
                },
            }
            resp = requests.post(f"{API_BASE}/pages", headers=self._headers(), json=body, timeout=15)
            resp.raise_for_status()
            page = resp.json()
            created.append({"id": page["id"], "url": page.get("url", ""), "title": task.title})
        return created


def _heading(text: str):
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": text}}]}}


def _paragraph(text: str):
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": text or "-"}}]}}


def _bullet(text: str):
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [{"text": {"content": text}}]},
    }
