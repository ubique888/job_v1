const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// Seeds
export const getSeeds = () => request<import("./types").Seed[]>("/v1/seeds");
export const createSeed = (data: { provider: string; company: string; board_url: string }) =>
  request<import("./types").Seed>("/v1/seeds", { method: "POST", body: JSON.stringify(data) });
export const deleteSeed = (id: string) =>
  request<void>(`/v1/seeds/${id}`, { method: "DELETE" });

// Search
export const createSearchRun = (data: {
  track: string;
  posted_within: string;
  provider_enabled: Record<string, boolean>;
  limit_per_provider: number;
}) =>
  request<{ run_id: string; state: string }>("/v1/search/runs", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const getSearchRun = (runId: string) =>
  request<import("./types").SearchRunResult>(`/v1/search/runs/${runId}`);

// Queue
export const getQueueItems = () =>
  request<import("./types").QueueItem[]>("/v1/queue/items");
export const addToQueue = (jobId: string, status = "bookmarked") =>
  request<import("./types").QueueItem>("/v1/queue/items", {
    method: "POST",
    body: JSON.stringify({ job_id: jobId, status }),
  });
export const updateQueueItem = (id: string, data: { status?: string; notes?: string }) =>
  request<import("./types").QueueItem>(`/v1/queue/items/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
