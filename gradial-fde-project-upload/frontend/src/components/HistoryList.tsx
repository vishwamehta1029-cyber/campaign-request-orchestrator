import type { CampaignRequest } from "../lib/types";

const STAGE_LABEL: Record<string, string> = {
  received: "Received",
  planning: "Planning",
  drafting_brief: "Drafting brief",
  creating_tasks: "Creating tasks",
  syncing_notion: "Syncing",
  complete: "Complete",
  error: "Error",
};

export function HistoryList({
  requests,
  selectedId,
  onSelect,
}: {
  requests: CampaignRequest[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="card">
      <h2>History</h2>
      {requests.length === 0 && <div className="empty-state">No requests yet — submit one to see the agent run.</div>}
      {requests.map((r) => (
        <button
          key={r.id}
          className={`history-item${r.id === selectedId ? " active" : ""}`}
          onClick={() => onSelect(r.id)}
          type="button"
        >
          <div className="title">{r.plan?.campaign_name ?? r.raw_text}</div>
          <div className="meta">
            {STAGE_LABEL[r.stage] ?? r.stage} · {new Date(r.created_at * 1000).toLocaleTimeString()}
          </div>
        </button>
      ))}
    </div>
  );
}
