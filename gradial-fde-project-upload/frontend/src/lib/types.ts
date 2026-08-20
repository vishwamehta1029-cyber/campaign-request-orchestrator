export type Stage =
  | "received"
  | "planning"
  | "drafting_brief"
  | "creating_tasks"
  | "syncing_notion"
  | "complete"
  | "error";

export type TraceType = "reasoning" | "tool_call" | "tool_result" | "system" | "error";

export interface TraceEntry {
  ts: number;
  type: TraceType;
  message: string;
  detail?: Record<string, unknown> | null;
}

export interface CampaignTask {
  title: string;
  owner_role: string;
  due_date?: string | null;
}

export interface CampaignPlan {
  campaign_name: string;
  objective: string;
  audience: string;
  channels: string[];
  key_dates: string;
  deliverables: string[];
  tasks: CampaignTask[];
}

export interface CampaignRequest {
  id: string;
  raw_text: string;
  stage: Stage;
  created_at: number;
  updated_at: number;
  plan: CampaignPlan | null;
  trace: TraceEntry[];
  notion_brief_url: string | null;
  notion_task_urls: string[];
  error: string | null;
}

export interface AdapterHealth {
  connected: boolean;
  detail: string;
}

export interface StatusResponse {
  agent_live: boolean;
  agent_model: string;
  workflow_tool: string;
  workflow_tool_health: AdapterHealth;
  rate_limit_per_hour: number | null;
}
