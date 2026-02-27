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
  request<{ discord_webhook_url: string | null }>("/v1/user/profile");

export const updateProfile = (data: { discord_webhook_url?: string }) =>
  request<{ discord_webhook_url: string | null }>("/v1/user/profile", {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const testDiscordWebhook = () =>
  request<{ status: string; message: string }>("/v1/user/profile/test-discord", {
    method: "POST",
  });
