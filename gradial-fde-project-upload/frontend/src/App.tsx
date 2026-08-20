import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./lib/api";
import type { CampaignRequest, StatusResponse } from "./lib/types";
import { StatusBar } from "./components/StatusBar";
import { StatTiles } from "./components/StatTiles";
import { RequestForm } from "./components/RequestForm";
import { HistoryList } from "./components/HistoryList";
import { PipelineStages } from "./components/PipelineStages";
import { TraceLog } from "./components/TraceLog";
import { PlanCard } from "./components/PlanCard";

const ACTIVE_STAGES = new Set(["received", "planning", "drafting_brief", "creating_tasks", "syncing_notion"]);

export default function App() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [requests, setRequests] = useState<CampaignRequest[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const pollTimer = useRef<number | null>(null);

  const refreshList = useCallback(async () => {
    try {
      const list = await api.listRequests();
      setRequests(list);
      setConnectionError(null);
      return list;
    } catch (e) {
      setConnectionError((e as Error).message);
      return [];
    }
  }, []);

  useEffect(() => {
    api.getStatus().then(setStatus).catch((e) => setConnectionError((e as Error).message));
    refreshList().then((list) => {
      if (list.length > 0) setSelectedId(list[0].id);
    });
  }, [refreshList]);

  // Poll while anything is in-flight so the pipeline/trace update live.
  useEffect(() => {
    const hasActive = requests.some((r) => ACTIVE_STAGES.has(r.stage));
    if (!hasActive) return;

    pollTimer.current = window.setInterval(() => {
      refreshList();
    }, 900);

    return () => {
      if (pollTimer.current) window.clearInterval(pollTimer.current);
    };
  }, [requests, refreshList]);

  const handleSubmit = async (text: string) => {
    setSubmitting(true);
    setSubmitError(null);
    try {
      const created = await api.createRequest(text);
      setRequests((prev) => [created, ...prev]);
      setSelectedId(created.id);
      setConnectionError(null);
    } catch (e) {
      setSubmitError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  const selected = requests.find((r) => r.id === selectedId) ?? null;

  return (
    <div className="app-shell">
      <div className="app-header">
        <div>
          <h1>Campaign Request Orchestrator</h1>
          <p>
            Drop in an ambiguous campaign request the way a stakeholder actually writes one. An LLM agent plans it,
            then executes real tool calls to stand it up in the workflow tool below — live trace included.
          </p>
        </div>
        <StatusBar status={status} />
      </div>

      {connectionError && (
        <div className="card" style={{ borderColor: "var(--status-critical)", marginBottom: 16 }}>
          Can't reach the backend at the configured API URL ({connectionError}). Make sure the FastAPI server is
          running — see the README.
        </div>
      )}

      <StatTiles requests={requests} />

      <div className="layout">
        <div>
          <RequestForm onSubmit={handleSubmit} submitting={submitting} rateLimitPerHour={status?.rate_limit_per_hour ?? null} />
          {submitError && (
            <div className="card" style={{ borderColor: "var(--status-critical)", fontSize: 13 }}>
              {submitError}
            </div>
          )}
          <HistoryList requests={requests} selectedId={selectedId} onSelect={setSelectedId} />
        </div>

        <div>
          {!selected && (
            <div className="card">
              <div className="empty-state">Submit a request on the left to watch the agent run end to end.</div>
            </div>
          )}

          {selected && (
            <>
              <div className="card">
                <h2>Pipeline</h2>
                <PipelineStages stage={selected.stage} />
              </div>

              <div className="card">
                <h2>Campaign plan</h2>
                <PlanCard request={selected} />
              </div>

              <div className="card">
                <h2>Agent trace</h2>
                <TraceLog trace={selected.trace} />
              </div>
            </>
          )}
        </div>
      </div>

      <div className="footer-note">
        Built as a demo of full-stack, LLM-agent-driven martech integration — plan → execute → sync, with a real
        adapter layer underneath.
      </div>
    </div>
  );
}
