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

// Subscriptions
export const getSubscriptions = () =>
  request<import("./types").Subscription[]>("/v1/subscriptions");

export const createSubscription = (data: {
  track: string;
  experience_level?: string | null;
  location_filter?: string | null;
  interval_minutes?: number;
}) =>
  request<import("./types").Subscription>("/v1/subscriptions", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateSubscription = (
  id: string,
  data: {
    track?: string;
    experience_level?: string | null;
    location_filter?: string | null;
    interval_minutes?: number;
    is_active?: boolean;
  },
) =>
  request<import("./types").Subscription>(`/v1/subscriptions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const deleteSubscription = (id: string) =>
  request<void>(`/v1/subscriptions/${id}`, { method: "DELETE" });

// Alerts
export const getAlerts = (subId: string) =>
  request<import("./types").Alert[]>(`/v1/subscriptions/${subId}/alerts`);

export const getUnreadAlertCount = () =>
  request<{ unread_count: number }>("/v1/alerts/count");

export const markAlertsRead = (subId: string) =>
  request<void>(`/v1/subscriptions/${subId}/alerts/mark-read`, { method: "POST" });

// Profile
export const getProfile = () =>
  request<import("./types").ProfileData>("/v1/user/profile");

export const updateProfile = (data: {
  discord_webhook_url?: string;
  llm_provider?: string;
  openai_api_key?: string;
}) =>
  request<import("./types").ProfileData>("/v1/user/profile", {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const testDiscordWebhook = () =>
  request<{ status: string; message: string }>("/v1/user/profile/test-discord", {
    method: "POST",
  });

export const testOpenaiKey = () =>
  request<{ status: string; message: string }>("/v1/user/profile/test-openai", {
    method: "POST",
  });

// Tracks
export const getTracks = () => request<string[]>("/v1/tracks");
export const getCustomTracks = () =>
  request<import("./types").CustomTrack[]>("/v1/custom-tracks");
export const createCustomTrack = (data: { name: string; keywords: string[] }) =>
  request<import("./types").CustomTrack>("/v1/custom-tracks", {
    method: "POST",
    body: JSON.stringify(data),
  });
export const deleteCustomTrack = (id: string) =>
  request<void>(`/v1/custom-tracks/${id}`, { method: "DELETE" });

// Summaries
export const getJobSummary = (jobId: string) =>
  request<import("./types").JobSummary>(`/v1/jobs/${jobId}/summary`);

export const createJobSummary = (jobId: string) =>
  request<import("./types").JobSummary>(`/v1/jobs/${jobId}/summary`, {
    method: "POST",
  });

export const getSummarizerHealth = () =>
  request<{ available: boolean; model: string }>("/v1/jobs/summarizer/health");
