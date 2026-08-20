"""Adapter contract for 'the workflow tool the agent writes into'.

This is the piece that maps directly onto the Gradial FDE job description:
'develop reusable tools, adapters, and configuration layers for scalable
onboarding'. Every enterprise customer has a different CMS / DAM / project
tool, so the agent orchestration layer (agent.py) never talks to Notion
directly -- it talks to this interface. Swapping Notion for Airtable,
HubSpot, or Asana later means writing one new adapter class; nothing else
in the system changes.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from ..models import CampaignPlan


class WorkflowToolAdapter(ABC):
    """Contract every martech/workflow integration must satisfy."""

    name: str = "base"

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Return {'connected': bool, 'detail': str} without raising."""
        raise NotImplementedError

    @abstractmethod
    def create_brief(self, plan: CampaignPlan) -> Dict[str, Any]:
        """Create the campaign brief record. Return {'id': str, 'url': str}."""
        raise NotImplementedError

    @abstractmethod
    def create_tasks(self, plan: CampaignPlan, brief_id: str) -> List[Dict[str, Any]]:
        """Create task records linked to the brief. Return list of {'id','url','title'}."""
        raise NotImplementedError
