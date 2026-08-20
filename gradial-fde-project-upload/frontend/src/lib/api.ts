import type { CampaignRequest, StatusResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) {
    const body = await resp.text().catch(() => "");
    let detail: string | null = null;
    try {
      detail = JSON.parse(body)?.detail ?? null;
    } catch {
      // not JSON — fall through to the raw body below
    }
    throw new Error(detail || body || `${resp.status} ${resp.statusText}`);
  }
  return resp.json();
}

export const api = {
  getStatus: () => req<StatusResponse>("/api/status"),
  listRequests: () => req<CampaignRequest[]>("/api/requests"),
  getRequest: (id: string) => req<CampaignRequest>(`/api/requests/${id}`),
  createRequest: (text: string) =>
    req<CampaignRequest>("/api/requests", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
};
