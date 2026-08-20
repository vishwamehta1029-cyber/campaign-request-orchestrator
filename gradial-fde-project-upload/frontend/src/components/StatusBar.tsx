import type { StatusResponse } from "../lib/types";

export function StatusBar({ status }: { status: StatusResponse | null }) {
  if (!status) {
    return (
      <div className="status-row">
        <span className="pill">
          <span className="dot dot--neutral" />
          Connecting…
        </span>
      </div>
    );
  }

  const agentDot = status.agent_live ? "dot--good" : "dot--warning";
  const workflowDot = status.workflow_tool_health.connected
    ? status.agent_live
      ? "dot--good"
      : "dot--warning"
    : "dot--critical";

  return (
    <div className="status-row">
      <span className="pill" title={status.agent_live ? `Live agent (${status.agent_model})` : "Deterministic mock planner — add OPENAI_API_KEY to go live"}>
        <span className={`dot ${agentDot}`} />
        Agent: {status.agent_live ? status.agent_model : "mock mode"}
      </span>
      <span className="pill" title={status.workflow_tool_health.detail}>
        <span className={`dot ${workflowDot}`} />
        {status.workflow_tool}
      </span>
    </div>
  );
}
