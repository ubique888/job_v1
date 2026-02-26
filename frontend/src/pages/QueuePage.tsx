import { useEffect, useState } from "react";
import * as api from "../lib/api";
import type { QueueItem, QueueStatus } from "../lib/types";

const STATUSES: QueueStatus[] = ["bookmarked", "in_queue", "applied", "rejected", "archived"];

function formatAge(hours: number | null): string {
  if (hours === null) return "Unknown";
  if (hours < 1) return "<1h ago";
  if (hours < 24) return `${Math.round(hours)}h ago`;
  if (hours < 168) return `${Math.round(hours / 24)}d ago`;
  return `${Math.round(hours / 168)}w ago`;
}

export default function QueuePage() {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<QueueStatus | "all">("all");

  useEffect(() => {
    api.getQueueItems().then(setItems).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const updateStatus = async (id: string, status: QueueStatus) => {
    const updated = await api.updateQueueItem(id, { status });
    setItems((prev) => prev.map((it) => (it.id === id ? updated : it)));
  };

  const updateNotes = async (id: string, notes: string) => {
    const updated = await api.updateQueueItem(id, { notes });
    setItems((prev) => prev.map((it) => (it.id === id ? updated : it)));
  };

  const filtered = filter === "all" ? items : items.filter((it) => it.status === filter);

  // Summary counts
  const counts = STATUSES.reduce(
    (acc, s) => {
      acc[s] = items.filter((it) => it.status === s).length;
      return acc;
    },
    {} as Record<QueueStatus, number>,
  );

  if (loading) {
    return (
      <div className="empty">
        <span className="spinner" /> Loading queue...
      </div>
    );
  }

  return (
    <div>
      <h2 style={{ marginBottom: "1rem" }}>Apply Queue</h2>

      {/* Summary */}
      <div className="stats-bar">
        <span>Total: <strong>{items.length}</strong></span>
        {STATUSES.map((s) => (
          <span key={s}>
            {s}: <strong>{counts[s]}</strong>
          </span>
        ))}
      </div>

      {/* Filter */}
      <div className="controls">
        <div className="field">
          <label>Filter Status</label>
          <select value={filter} onChange={(e) => setFilter(e.target.value as QueueStatus | "all")}>
            <option value="all">All</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="empty">
          <p>No items in queue. Bookmark or add jobs from the Search page.</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Company</th>
                <th>Role</th>
                <th>Location</th>
                <th>Posted</th>
                <th>Status</th>
                <th>Notes</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => {
                const job = item.job;
                return (
                  <tr key={item.id}>
                    <td>{job?.company ?? "—"}</td>
                    <td>{job?.title ?? "—"}</td>
                    <td>{job?.location || "—"}</td>
                    <td>{formatAge(job?.posted_age_hours ?? null)}</td>
                    <td>
                      <select
                        className={`badge badge-${item.status}`}
                        value={item.status}
                        onChange={(e) => updateStatus(item.id, e.target.value as QueueStatus)}
                        style={{ background: "transparent", border: "none", cursor: "pointer", color: "inherit" }}
                      >
                        {STATUSES.map((s) => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <input
                        type="text"
                        className="notes-input"
                        defaultValue={item.notes}
                        placeholder="Add notes..."
                        onBlur={(e) => {
                          if (e.target.value !== item.notes) {
                            updateNotes(item.id, e.target.value);
                          }
                        }}
                      />
                    </td>
                    <td>
                      {job?.apply_url ? (
                        <a href={job.apply_url} target="_blank" rel="noopener noreferrer" className="btn-secondary btn-sm" style={{ display: "inline-block", textDecoration: "none" }}>
                          Apply
                        </a>
                      ) : (
                        <span className="badge badge-unknown">no link</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
