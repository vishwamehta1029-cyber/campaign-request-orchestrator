import type { CampaignRequest } from "../lib/types";

function computeStats(requests: CampaignRequest[]) {
  const total = requests.length;
  const completed = requests.filter((r) => r.stage === "complete");
  const tasksAutomated = requests.reduce((sum, r) => sum + r.notion_task_urls.length, 0);
  const errors = requests.filter((r) => r.stage === "error").length;

  const avgSeconds =
    completed.length > 0
      ? completed.reduce((sum, r) => sum + (r.updated_at - r.created_at), 0) / completed.length
      : null;

  const successRate = total > 0 ? Math.round(((total - errors) / total) * 100) : null;

  return { total, tasksAutomated, avgSeconds, successRate };
}

export function StatTiles({ requests }: { requests: CampaignRequest[] }) {
  const { total, tasksAutomated, avgSeconds, successRate } = computeStats(requests);

  return (
    <div className="stat-grid">
      <div className="stat-tile">
        <div className="label">Requests Processed</div>
        <div className="value">{total}</div>
        <div className="sub">since this session started</div>
      </div>
      <div className="stat-tile">
        <div className="label">Tasks Automated</div>
        <div className="value">{tasksAutomated}</div>
        <div className="sub">written into the workflow tool</div>
      </div>
      <div className="stat-tile">
        <div className="label">Avg Cycle Time</div>
        <div className="value">{avgSeconds === null ? "—" : `${avgSeconds.toFixed(1)}s`}</div>
        <div className="sub">request → synced brief</div>
      </div>
      <div className="stat-tile">
        <div className="label">Success Rate</div>
        <div className="value">{successRate === null ? "—" : `${successRate}%`}</div>
        <div className="sub">completed without error</div>
      </div>
    </div>
  );
}
