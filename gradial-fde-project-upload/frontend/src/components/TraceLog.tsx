import type { TraceEntry, TraceType } from "../lib/types";

const ICONS: Record<TraceType, string> = {
  reasoning: "◆",
  tool_call: "→",
  tool_result: "✓",
  system: "•",
  error: "!",
};

function relativeTime(ts: number) {
  return new Date(ts * 1000).toLocaleTimeString();
}

export function TraceLog({ trace }: { trace: TraceEntry[] }) {
  if (trace.length === 0) {
    return <div className="empty-state">No activity yet.</div>;
  }
  return (
    <div className="trace-log">
      {trace.map((t, i) => (
        <div className="trace-entry" key={i}>
          <div className={`icon ${t.type}`}>{ICONS[t.type]}</div>
          <div>
            <span className="message">{t.message}</span>
            <span className="ts">{relativeTime(t.ts)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
