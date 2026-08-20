import type { Stage } from "../lib/types";

const STAGES: { key: Stage; label: string }[] = [
  { key: "received", label: "Received" },
  { key: "planning", label: "Planning" },
  { key: "drafting_brief", label: "Drafting brief" },
  { key: "creating_tasks", label: "Creating tasks" },
  { key: "syncing_notion", label: "Syncing" },
  { key: "complete", label: "Complete" },
];

export function PipelineStages({ stage }: { stage: Stage }) {
  const currentIndex = STAGES.findIndex((s) => s.key === stage);
  const isError = stage === "error";
  const isComplete = stage === "complete";

  return (
    <div className="pipeline">
      {STAGES.map((s, i) => {
        const done = !isError && (isComplete || i < currentIndex);
        const active = !isError && !isComplete && i === currentIndex;
        const cls = isError && i === currentIndex ? "error" : done ? "done" : active ? "active" : "";
        return (
          <div className="pipeline-step-wrap" key={s.key} style={{ display: "contents" }}>
            <div className={`pipeline-step ${cls}`}>
              <div className="node">{done ? "✓" : i + 1}</div>
              <div className="label">{s.label}</div>
            </div>
            {i < STAGES.length - 1 && <div className={`pipeline-connector ${done ? "done" : ""}`} />}
          </div>
        );
      })}
      {isError && (
        <>
          <div className="pipeline-connector" />
          <div className="pipeline-step error">
            <div className="node">!</div>
            <div className="label">Error</div>
          </div>
        </>
      )}
    </div>
  );
}
