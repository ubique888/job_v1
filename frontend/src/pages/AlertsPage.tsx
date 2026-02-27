import { useEffect, useState } from "react";
import * as api from "../lib/api";
import type { Subscription, Alert, Job, Track, ExperienceLevel } from "../lib/types";

const TRACKS: Track[] = ["Backend", "Frontend", "Fullstack", "DevOps", "Data", "ML", "AI Agent", "Consulting"];
const LEVELS: (ExperienceLevel | "")[] = ["", "intern", "entry-level", "higher-level"];
const LOCATIONS = ["", "New York", "Seattle", "Los Angeles", "San Francisco", "Boston", "London", "Paris", "Remote", "Other"];
const INTERVALS = [
  { label: "15 min", value: 15 },
  { label: "30 min", value: 30 },
  { label: "1 hour", value: 60 },
  { label: "4 hours", value: 240 },
  { label: "12 hours", value: 720 },
  { label: "24 hours", value: 1440 },
];

function formatAge(hours: number | null): string {
  if (hours === null) return "Unknown";
  if (hours < 1) return "<1h ago";
  if (hours < 24) return `${Math.round(hours)}h ago`;
  if (hours < 168) return `${Math.round(hours / 24)}d ago`;
  return `${Math.round(hours / 168)}w ago`;
}

function formatInterval(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  if (minutes < 1440) return `${minutes / 60}h`;
  return `${minutes / 1440}d`;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function AlertsPage() {
  // Subscriptions
  const [subs, setSubs] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Create form
  const [newTrack, setNewTrack] = useState<Track>("Backend");
  const [newLevel, setNewLevel] = useState<ExperienceLevel | "">("");
  const [newLocation, setNewLocation] = useState("");
  const [newInterval, setNewInterval] = useState(60);
  const [creating, setCreating] = useState(false);

  // Alert feed
  const [expandedSub, setExpandedSub] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(false);

  // Detail drawer
  const [detail, setDetail] = useState<Job | null>(null);

  // Discord webhook
  const [webhookUrl, setWebhookUrl] = useState("");
  const [webhookSaved, setWebhookSaved] = useState("");
  const [webhookSaving, setWebhookSaving] = useState(false);
  const [webhookTesting, setWebhookTesting] = useState(false);
  const [webhookMsg, setWebhookMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  // Load subscriptions + profile
  useEffect(() => {
    api
      .getSubscriptions()
      .then(setSubs)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));

    api.getProfile().then((p) => {
      const url = p.discord_webhook_url || "";
      setWebhookUrl(url);
      setWebhookSaved(url);
    });
  }, []);

  // Load alerts when expanding a subscription
  const toggleAlerts = async (subId: string) => {
    if (expandedSub === subId) {
      setExpandedSub(null);
      setAlerts([]);
      return;
    }
    setExpandedSub(subId);
    setAlertsLoading(true);
    try {
      const data = await api.getAlerts(subId);
      setAlerts(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setAlertsLoading(false);
    }
  };

  // Create subscription
  const handleCreate = async () => {
    setCreating(true);
    setError("");
    try {
      const sub = await api.createSubscription({
        track: newTrack,
        experience_level: newLevel || null,
        location_filter: newLocation || null,
        interval_minutes: newInterval,
      });
      setSubs((prev) => [sub, ...prev]);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setCreating(false);
    }
  };

  // Toggle active
  const toggleActive = async (sub: Subscription) => {
    try {
      const updated = await api.updateSubscription(sub.id, {
        is_active: !sub.is_active,
      });
      setSubs((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    } catch (e: any) {
      setError(e.message);
    }
  };

  // Delete subscription
  const handleDelete = async (subId: string) => {
    try {
      await api.deleteSubscription(subId);
      setSubs((prev) => prev.filter((s) => s.id !== subId));
      if (expandedSub === subId) {
        setExpandedSub(null);
        setAlerts([]);
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  // Mark all alerts read
  const handleMarkRead = async (subId: string) => {
    try {
      await api.markAlertsRead(subId);
      setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })));
      setSubs((prev) =>
        prev.map((s) => (s.id === subId ? { ...s, unread_count: 0 } : s)),
      );
    } catch (e: any) {
      setError(e.message);
    }
  };

  // Save webhook URL
  const saveWebhook = async () => {
    setWebhookSaving(true);
    setWebhookMsg(null);
    try {
      const res = await api.updateProfile({ discord_webhook_url: webhookUrl });
      const saved = res.discord_webhook_url || "";
      setWebhookSaved(saved);
      setWebhookUrl(saved);
      setWebhookMsg({ type: "ok", text: webhookUrl ? "Webhook saved!" : "Webhook removed." });
    } catch (e: any) {
      setWebhookMsg({ type: "err", text: e.message });
    } finally {
      setWebhookSaving(false);
    }
  };

  // Test webhook
  const testWebhook = async () => {
    setWebhookTesting(true);
    setWebhookMsg(null);
    try {
      await api.testDiscordWebhook();
      setWebhookMsg({ type: "ok", text: "Test message sent! Check your Discord channel." });
    } catch (e: any) {
      setWebhookMsg({ type: "err", text: `Test failed: ${e.message}` });
    } finally {
      setWebhookTesting(false);
    }
  };

  return (
    <div>
      <h2 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>Job Alerts</h2>

      {/* Discord webhook settings */}
      <div className="webhook-settings">
        <div className="webhook-header">
          <h3>Discord Notifications</h3>
          <span className="webhook-status">
            {webhookSaved ? (
              <span className="webhook-active">Connected</span>
            ) : (
              <span className="webhook-inactive">Not configured</span>
            )}
          </span>
        </div>
        <p className="webhook-desc">
          Get notified in Discord when new matching jobs are found. Paste your channel's webhook URL below.
        </p>
        <div className="webhook-form">
          <input
            type="url"
            placeholder="https://discord.com/api/webhooks/..."
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
            className="webhook-input"
          />
          <button
            className="btn-primary btn-sm"
            onClick={saveWebhook}
            disabled={webhookSaving || webhookUrl === webhookSaved}
          >
            {webhookSaving ? "Saving..." : "Save"}
          </button>
          {webhookSaved && (
            <button
              className="btn-secondary btn-sm"
              onClick={testWebhook}
              disabled={webhookTesting}
            >
              {webhookTesting ? "Sending..." : "Test"}
            </button>
          )}
        </div>
        {webhookMsg && (
          <p className={`webhook-msg ${webhookMsg.type === "ok" ? "webhook-msg-ok" : "webhook-msg-err"}`}>
            {webhookMsg.text}
          </p>
        )}
      </div>

      {/* Create subscription form */}
      <div className="alert-create-form">
        <h3>Create Alert</h3>
        <div className="alert-form-row">
          <div className="field">
            <label>Track</label>
            <select value={newTrack} onChange={(e) => setNewTrack(e.target.value as Track)}>
              {TRACKS.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Level</label>
            <select value={newLevel} onChange={(e) => setNewLevel(e.target.value as ExperienceLevel | "")}>
              <option value="">Any</option>
              <option value="intern">Intern</option>
              <option value="entry-level">Entry Level</option>
              <option value="higher-level">Higher Level</option>
            </select>
          </div>

          <div className="field">
            <label>Location</label>
            <select value={newLocation} onChange={(e) => setNewLocation(e.target.value)}>
              <option value="">Any</option>
              {LOCATIONS.filter(Boolean).map((loc) => (
                <option key={loc} value={loc}>{loc}</option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Check Every</label>
            <select value={newInterval} onChange={(e) => setNewInterval(Number(e.target.value))}>
              {INTERVALS.map((i) => (
                <option key={i.value} value={i.value}>{i.label}</option>
              ))}
            </select>
          </div>

          <button className="btn-primary" onClick={handleCreate} disabled={creating}>
            {creating ? "Creating..." : "Create Alert"}
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* Subscriptions list */}
      {loading ? (
        <p style={{ color: "#8b949e", textAlign: "center", padding: "2rem" }}>Loading...</p>
      ) : subs.length === 0 ? (
        <div className="empty">
          <p>No alerts yet. Create one above to start monitoring for new jobs.</p>
        </div>
      ) : (
        <div className="subs-list">
          {subs.map((sub) => (
            <div key={sub.id} className="sub-card">
              <div className="sub-card-header">
                <div className="sub-card-info">
                  <span className="sub-track-badge">{sub.track}</span>
                  {sub.experience_level && (
                    <span className={`badge badge-level-${sub.experience_level}`}>
                      {sub.experience_level}
                    </span>
                  )}
                  {sub.location_filter && (
                    <span className="sub-location-tag">{sub.location_filter}</span>
                  )}
                  <span className="sub-interval">every {formatInterval(sub.interval_minutes)}</span>
                  {sub.last_checked_at && (
                    <span className="sub-last-checked">checked {timeAgo(sub.last_checked_at)}</span>
                  )}
                </div>
                <div className="sub-card-actions">
                  {sub.unread_count > 0 && (
                    <span className="alert-count-badge">{sub.unread_count} new</span>
                  )}
                  <button
                    className={`btn-sm ${sub.is_active ? "btn-active-toggle" : "btn-inactive-toggle"}`}
                    onClick={() => toggleActive(sub)}
                  >
                    {sub.is_active ? "Active" : "Paused"}
                  </button>
                  <button
                    className="btn-secondary btn-sm"
                    onClick={() => toggleAlerts(sub.id)}
                  >
                    {expandedSub === sub.id ? "Hide" : "View"} Alerts
                  </button>
                  <button
                    className="btn-danger btn-sm"
                    onClick={() => handleDelete(sub.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>

              {/* Expanded alert feed */}
              {expandedSub === sub.id && (
                <div className="alert-feed">
                  {alertsLoading ? (
                    <p style={{ color: "#8b949e", padding: "0.5rem" }}>Loading alerts...</p>
                  ) : alerts.length === 0 ? (
                    <p style={{ color: "#8b949e", padding: "0.5rem", fontSize: "0.85rem" }}>
                      No alerts yet. The background checker will find matches on its next run.
                    </p>
                  ) : (
                    <>
                      <div className="alert-feed-header">
                        <span>{alerts.length} alert{alerts.length !== 1 ? "s" : ""}</span>
                        {alerts.some((a) => !a.is_read) && (
                          <button
                            className="btn-secondary btn-sm"
                            onClick={() => handleMarkRead(sub.id)}
                          >
                            Mark All Read
                          </button>
                        )}
                      </div>
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th></th>
                              <th>Company</th>
                              <th>Role</th>
                              <th>Location</th>
                              <th>Level</th>
                              <th>YOE</th>
                              <th>Posted</th>
                              <th>Apply</th>
                            </tr>
                          </thead>
                          <tbody>
                            {alerts.map((alert) => {
                              const job = alert.job;
                              if (!job) return null;
                              return (
                                <tr key={alert.id} className={alert.is_read ? "" : "alert-unread"}>
                                  <td>{!alert.is_read && <span className="unread-dot" />}</td>
                                  <td>{job.company}</td>
                                  <td>
                                    <a
                                      href="#"
                                      onClick={(e) => {
                                        e.preventDefault();
                                        setDetail(job);
                                      }}
                                    >
                                      {job.title}
                                    </a>
                                  </td>
                                  <td>{job.location || "\u2014"}</td>
                                  <td>
                                    <span className={`badge badge-level-${job.experience_level || "entry-level"}`}>
                                      {job.experience_level || "entry-level"}
                                    </span>
                                  </td>
                                  <td>{job.yoe_min !== null ? `${job.yoe_min}+` : "\u2014"}</td>
                                  <td>{formatAge(job.posted_age_hours)}</td>
                                  <td>
                                    {job.apply_url ? (
                                      <a href={job.apply_url} target="_blank" rel="noopener noreferrer">
                                        Apply
                                      </a>
                                    ) : (
                                      "\u2014"
                                    )}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Detail drawer */}
      {detail && (
        <>
          <div className="detail-overlay" onClick={() => setDetail(null)} />
          <div className="detail-drawer">
            <button className="btn-secondary btn-sm" onClick={() => setDetail(null)} style={{ marginBottom: "1rem" }}>
              Close
            </button>
            <h2>{detail.title}</h2>
            <div className="detail-meta">
              <span>{detail.company}</span>
              <span>{detail.location || "No location"}</span>
              <span>{detail.platform}</span>
              <span>{formatAge(detail.posted_age_hours)}</span>
              {detail.experience_level && (
                <span className={`badge badge-level-${detail.experience_level}`}>
                  {detail.experience_level}
                </span>
              )}
              {detail.yoe_min !== null && (
                <span>{detail.yoe_min}+ years experience</span>
              )}
            </div>
            {detail.apply_url && (
              <p style={{ marginBottom: "1rem" }}>
                <a href={detail.apply_url} target="_blank" rel="noopener noreferrer">
                  Open Application Page
                </a>
              </p>
            )}
            {detail.jd_raw_text ? (
              <div className="detail-jd">{detail.jd_raw_text}</div>
            ) : (
              <p style={{ color: "#8b949e" }}>No job description available.</p>
            )}
            <p style={{ marginTop: "1rem", fontSize: "0.75rem", color: "#8b949e" }}>
              Source: <a href={detail.source_url} target="_blank" rel="noopener noreferrer">{detail.source_url}</a>
            </p>
          </div>
        </>
      )}
    </div>
  );
}
