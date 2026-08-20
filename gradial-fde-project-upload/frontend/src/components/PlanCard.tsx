import type { CampaignRequest } from "../lib/types";

export function PlanCard({ request }: { request: CampaignRequest }) {
  const { plan } = request;
  if (!plan) {
    return <div className="empty-state">Plan not drafted yet.</div>;
  }

  return (
    <div>
      <div className="plan-grid">
        <div className="plan-field">
          <div className="k">Objective</div>
          <div className="v">{plan.objective}</div>
        </div>
        <div className="plan-field">
          <div className="k">Audience</div>
          <div className="v">{plan.audience}</div>
        </div>
        <div className="plan-field">
          <div className="k">Key dates</div>
          <div className="v">{plan.key_dates}</div>
        </div>
        <div className="plan-field">
          <div className="k">Channels</div>
          <div className="tag-row">
            {plan.channels.map((c) => (
              <span className="tag" key={c}>
                {c}
              </span>
            ))}
          </div>
        </div>
      </div>

      <table className="task-table">
        <thead>
          <tr>
            <th>Task</th>
            <th>Owner</th>
            <th>Due</th>
          </tr>
        </thead>
        <tbody>
          {plan.tasks.map((t, i) => (
            <tr key={i}>
              <td>{t.title}</td>
              <td>{t.owner_role}</td>
              <td>{t.due_date ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {(request.notion_brief_url || request.notion_task_urls.length > 0) && (
        <div className="links-row">
          {request.notion_brief_url && (
            <a className="link-btn" href={request.notion_brief_url} target="_blank" rel="noreferrer">
              Open brief ↗
            </a>
          )}
          {request.notion_task_urls.length > 0 && (
            <a className="link-btn" href={request.notion_task_urls[0]} target="_blank" rel="noreferrer">
              Open first task ↗
            </a>
          )}
        </div>
      )}

      {request.error && (
        <div className="v" style={{ color: "var(--status-critical)", marginTop: 10 }}>
          {request.error}
        </div>
      )}
    </div>
  );
}
