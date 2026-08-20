import { useState } from "react";

const EXAMPLES = [
  "We need a paid social and email campaign for our fall promo, targeting existing customers, launch by next Friday",
  "Set up a re-engagement campaign for lapsed customers ahead of the holiday season",
  "Launch an SEO and content push to support the new product line by end of quarter",
];

export function RequestForm({
  onSubmit,
  submitting,
  rateLimitPerHour,
}: {
  onSubmit: (text: string) => void;
  submitting: boolean;
  rateLimitPerHour?: number | null;
}) {
  const [text, setText] = useState("");

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed || submitting) return;
    onSubmit(trimmed);
    setText("");
  };

  return (
    <div className="card">
      <h2>New campaign request</h2>
      <textarea
        className="request-input"
        placeholder="Describe the campaign in plain language, the way a stakeholder actually would…"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
        }}
      />
      <div className="example-chips">
        {EXAMPLES.map((ex) => (
          <button key={ex} className="chip" onClick={() => setText(ex)} type="button">
            {ex.length > 46 ? ex.slice(0, 46) + "…" : ex}
          </button>
        ))}
      </div>
      <button className="btn-primary" onClick={submit} disabled={submitting || !text.trim()}>
        {submitting ? "Dispatching to agent…" : "Submit to agent"}
      </button>
      {rateLimitPerHour != null && (
        <div style={{ fontSize: 11.5, color: "var(--text-muted)", marginTop: 8 }}>
          Public demo, running with a real AI model — capped at {rateLimitPerHour} requests/hour per visitor.
        </div>
      )}
    </div>
  );
}
