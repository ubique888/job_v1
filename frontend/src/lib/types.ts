export type Track = "Backend" | "Frontend" | "Fullstack" | "DevOps" | "Data" | "ML" | "AI Agent" | "Consulting";
export type PostedWithin = "24h" | "48h" | "7d" | "30d";
export type Provider = "greenhouse" | "lever";
export type ApplyUrlStatus = "direct" | "derived" | "unknown";
export type QueueStatus = "bookmarked" | "in_queue" | "applied" | "rejected" | "archived";
export type ExperienceLevel = "intern" | "entry-level" | "higher-level";

export interface Seed {
  id: string;
  provider: Provider;
  company: string;
  board_url: string;
  created_at: string;
}

export interface Evidence {
  type: string;
  text: string;
}

export interface Job {
  id: string;
  company: string;
  title: string;
  location: string | null;
  platform: string;
  source_url: string;
  apply_url: string | null;
  apply_url_status: ApplyUrlStatus;
  posted_date: string | null;
  posted_age_hours: number | null;
  jd_raw_text: string | null;
  track: string | null;
  experience_level: ExperienceLevel | null;
  yoe_min: number | null;
  scrape_ts: string;
  evidence: Evidence[];
}

export interface SearchRunResult {
  run_id: string;
  state: string;
  track: string;
  posted_within: string;
  started_at: string;
  finished_at: string | null;
  stats: Record<string, unknown>;
  discovered_jobs: Job[];
}

export interface QueueItem {
  id: string;
  job_id: string;
  status: QueueStatus;
  notes: string;
  created_at: string;
  updated_at: string;
  job: Job | null;
}

export interface Subscription {
  id: string;
  track: string;
  experience_level: string | null;
  location_filter: string | null;
  is_active: boolean;
  interval_minutes: number;
  last_checked_at: string | null;
  created_at: string;
  updated_at: string;
  unread_count: number;
}

export interface Alert {
  id: string;
  subscription_id: string;
  job_id: string;
  is_read: boolean;
  created_at: string;
  job: Job | null;
}
