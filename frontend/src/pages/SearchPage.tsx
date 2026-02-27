import React, { useCallback, useEffect, useMemo, useState } from "react";
import * as api from "../lib/api";
import { CATEGORIES, DEFAULT_SEEDS, getBoardUrl } from "../lib/defaultSeeds";
import type { Job, Seed, Track, PostedWithin, SearchRunResult, ExperienceLevel } from "../lib/types";

type SortKey = "company" | "title" | "location" | "posted_age_hours";
type SortDir = "asc" | "desc";
type LocationFilter = "All" | "New York" | "Seattle" | "Los Angeles" | "San Francisco" | "Boston" | "London" | "Paris" | "Remote" | "Other";
type LevelFilter = "All" | ExperienceLevel;

const TRACKS: Track[] = ["Backend", "Frontend", "Fullstack", "DevOps", "Data", "ML", "AI Agent", "Consulting"];
const POSTED: PostedWithin[] = ["24h", "48h", "7d", "30d"];
const LOCATIONS: LocationFilter[] = ["All", "New York", "Seattle", "Los Angeles", "San Francisco", "Boston", "London", "Paris", "Remote", "Other"];

const LOCATION_PATTERNS: Record<string, string[]> = {
  "New York": ["new york", "nyc", "brooklyn", "manhattan"],
  "Seattle": ["seattle", "bellevue", "redmond"],
  "Los Angeles": ["los angeles", "la,", "la ", "santa monica", "culver city", "venice, ca", "hollywood"],
  "San Francisco": ["san francisco", "sf,", "sf ", "bay area", "palo alto", "mountain view", "sunnyvale", "san jose", "san mateo", "menlo park", "redwood city", "cupertino", "santa clara"],
  "Boston": ["boston", "cambridge, ma", "somerville, ma", "waltham"],
  "London": ["london"],
  "Paris": ["paris"],
  "Remote": ["remote"],
};

function matchesLocation(location: string | null, filter: LocationFilter): boolean {
  if (filter === "All") return true;
  const loc = (location || "").toLowerCase();
  if (filter === "Other") {
    // "Other" = doesn't match any named city or remote
    return !Object.values(LOCATION_PATTERNS).some((patterns) =>
      patterns.some((p) => loc.includes(p))
    );
  }
  const patterns = LOCATION_PATTERNS[filter];
  return patterns ? patterns.some((p) => loc.includes(p)) : false;
}

function formatAge(hours: number | null): string {
  if (hours === null) return "Unknown";
  if (hours < 1) return "<1h ago";
  if (hours < 24) return `${Math.round(hours)}h ago`;
  if (hours < 168) return `${Math.round(hours / 24)}d ago`;
  return `${Math.round(hours / 168)}w ago`;
}

export default function SearchPage() {
  const [track, setTrack] = useState<Track>("Backend");
  const [postedWithin, setPostedWithin] = useState<PostedWithin>("7d");
  const [ghEnabled, setGhEnabled] = useState(true);
  const [leverEnabled, setLeverEnabled] = useState(true);

  // Seeds
  const [seeds, setSeeds] = useState<Seed[]>([]);
  const [showSeeds, setShowSeeds] = useState(false);
  const [seedProvider, setSeedProvider] = useState<"greenhouse" | "lever">("greenhouse");
  const [seedCompany, setSeedCompany] = useState("");
  const [seedUrl, setSeedUrl] = useState("");

  // Presets
  const [selectedPresets, setSelectedPresets] = useState<Set<string>>(new Set());
  const [addingPresets, setAddingPresets] = useState(false);

  const seedUrls = useMemo(() => new Set(seeds.map((s) => s.board_url)), [seeds]);

  const togglePreset = (key: string) => {
    setSelectedPresets((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const addSelectedPresets = async () => {
    setAddingPresets(true);
    try {
      for (const key of selectedPresets) {
        const ds = DEFAULT_SEEDS.find((d) => `${d.provider}:${d.token}` === key);
        if (!ds) continue;
        const boardUrl = getBoardUrl(ds);
        if (seedUrls.has(boardUrl)) continue;
        const seed = await api.createSeed({
          provider: ds.provider,
          company: ds.company,
          board_url: boardUrl,
        });
        setSeeds((prev) => [seed, ...prev]);
      }
      setSelectedPresets(new Set());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setAddingPresets(false);
    }
  };

  // Search
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<SearchRunResult | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);

  // Detail
  const [detail, setDetail] = useState<Job | null>(null);

  // Inline preview
  const [expandedJob, setExpandedJob] = useState<string | null>(null);

  // Location filter
  const [locationFilter, setLocationFilter] = useState<LocationFilter>("All");

  // Level filter
  const [levelFilter, setLevelFilter] = useState<LevelFilter>("All");

  // Sort
  const [sortBy, setSortBy] = useState<SortKey | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const toggleSort = (key: SortKey) => {
    if (sortBy !== key) {
      setSortBy(key);
      setSortDir("asc");
    } else if (sortDir === "asc") {
      setSortDir("desc");
    } else {
      setSortBy(null);
      setSortDir("asc");
    }
  };

  const sortIndicator = (key: SortKey) =>
    sortBy === key ? (sortDir === "asc" ? " \u25B2" : " \u25BC") : "";

  const sortedJobs = useMemo(() => {
    if (!sortBy) return jobs;
    return [...jobs].sort((a, b) => {
      const av = a[sortBy];
      const bv = b[sortBy];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      let cmp: number;
      if (typeof av === "number" && typeof bv === "number") {
        cmp = av - bv;
      } else {
        cmp = String(av).localeCompare(String(bv));
      }
      return sortDir === "desc" ? -cmp : cmp;
    });
  }, [jobs, sortBy, sortDir]);

  const filteredJobs = useMemo(() => {
    let result = sortedJobs;
    if (locationFilter !== "All") {
      result = result.filter((job) => matchesLocation(job.location, locationFilter));
    }
    if (levelFilter !== "All") {
      result = result.filter((job) => job.experience_level === levelFilter);
    }
    return result;
  }, [sortedJobs, locationFilter, levelFilter]);

  // Load seeds on mount
  useEffect(() => {
    api.getSeeds().then(setSeeds).catch(() => {});
  }, []);

  const addSeed = async () => {
    if (!seedCompany.trim() || !seedUrl.trim()) return;
    try {
      const seed = await api.createSeed({
        provider: seedProvider,
        company: seedCompany.trim(),
        board_url: seedUrl.trim(),
      });
      setSeeds((prev) => [seed, ...prev]);
      setSeedCompany("");
      setSeedUrl("");
    } catch (e: any) {
      setError(e.message);
    }
  };

  const removeSeed = async (id: string) => {
    await api.deleteSeed(id);
    setSeeds((prev) => prev.filter((s) => s.id !== id));
  };

  const runSearch = async () => {
    setLoading(true);
    setError("");
    setJobs([]);
    setResult(null);
    setSortBy(null);
    setSortDir("asc");
    setLocationFilter("All");
    setLevelFilter("All");
    try {
      const { run_id } = await api.createSearchRun({
        track,
        posted_within: postedWithin,
        provider_enabled: { greenhouse: ghEnabled, lever: leverEnabled },
        limit_per_provider: 50,
      });
      const data = await api.getSearchRun(run_id);
      setResult(data);
      setJobs(data.discovered_jobs);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const addToQueue = useCallback(async (jobId: string) => {
    try {
      await api.addToQueue(jobId);
    } catch (e: any) {
      if (!e.message.includes("409")) setError(e.message);
    }
  }, []);

  const copyLink = (url: string) => {
    navigator.clipboard.writeText(url);
  };

  const hasSeeds = seeds.length > 0;

  return (
    <div>
      {/* Controls */}
      <div className="controls">
        <div className="field">
          <label>Applying For</label>
          <select value={track} onChange={(e) => setTrack(e.target.value as Track)}>
            {TRACKS.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Posted Within</label>
          <select value={postedWithin} onChange={(e) => setPostedWithin(e.target.value as PostedWithin)}>
            {POSTED.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Location</label>
          <select value={locationFilter} onChange={(e) => setLocationFilter(e.target.value as LocationFilter)}>
            {LOCATIONS.map((loc) => (
              <option key={loc} value={loc}>{loc}</option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Level</label>
          <select value={levelFilter} onChange={(e) => setLevelFilter(e.target.value as LevelFilter)}>
            <option value="All">All</option>
            <option value="intern">Intern</option>
            <option value="entry-level">Entry Level</option>
            <option value="higher-level">Higher Level</option>
          </select>
        </div>

        <div className="field">
          <label>Providers</label>
          <div style={{ display: "flex", gap: "0.75rem", padding: "0.5rem 0" }}>
            <label style={{ fontSize: "0.85rem", display: "flex", gap: "0.3rem", alignItems: "center" }}>
              <input type="checkbox" checked={ghEnabled} onChange={(e) => setGhEnabled(e.target.checked)} />
              Greenhouse
            </label>
            <label style={{ fontSize: "0.85rem", display: "flex", gap: "0.3rem", alignItems: "center" }}>
              <input type="checkbox" checked={leverEnabled} onChange={(e) => setLeverEnabled(e.target.checked)} />
              Lever
            </label>
          </div>
        </div>

        <button className="btn-secondary" onClick={() => setShowSeeds(!showSeeds)}>
          {showSeeds ? "Hide" : "Manage"} Sources ({seeds.length})
        </button>

        <button
          className="btn-primary"
          disabled={!hasSeeds || loading}
          onClick={runSearch}
        >
          {loading ? <><span className="spinner" /> Searching...</> : "Run Search"}
        </button>
      </div>

      {/* Seeds panel */}
      {showSeeds && (
        <div className="seeds-panel">
          <h3>Company Sources (Seeds)</h3>
          <div className="seed-form">
            <select
              value={seedProvider}
              onChange={(e) => setSeedProvider(e.target.value as "greenhouse" | "lever")}
              style={{ minWidth: 120 }}
            >
              <option value="greenhouse">Greenhouse</option>
              <option value="lever">Lever</option>
            </select>
            <input
              type="text"
              placeholder="Company name"
              value={seedCompany}
              onChange={(e) => setSeedCompany(e.target.value)}
              style={{ minWidth: 140 }}
            />
            <input
              type="url"
              placeholder={
                seedProvider === "greenhouse"
                  ? "https://boards.greenhouse.io/company"
                  : "https://jobs.lever.co/company"
              }
              value={seedUrl}
              onChange={(e) => setSeedUrl(e.target.value)}
              style={{ flex: 1, minWidth: 250 }}
            />
            <button className="btn-primary btn-sm" onClick={addSeed}>
              Add Seed
            </button>
          </div>
          {seeds.length === 0 ? (
            <p style={{ color: "#8b949e", fontSize: "0.85rem" }}>
              No seeds yet. Add a company board URL above or select from popular companies below.
            </p>
          ) : (
            <ul className="seed-list">
              {seeds.map((s) => (
                <li key={s.id} className="seed-item">
                  <div>
                    <span className={`seed-provider ${s.provider}`}>{s.provider}</span>
                    <strong>{s.company}</strong>
                    <span style={{ color: "#8b949e", marginLeft: "0.5rem", fontSize: "0.8rem" }}>
                      {s.board_url}
                    </span>
                  </div>
                  <button className="btn-danger btn-sm" onClick={() => removeSeed(s.id)}>
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}

          {/* Preset companies */}
          <div className="presets-section">
            <div className="presets-header">
              <h4>Popular Companies</h4>
              {selectedPresets.size > 0 && (
                <button
                  className="btn-primary btn-sm"
                  onClick={addSelectedPresets}
                  disabled={addingPresets}
                >
                  {addingPresets ? "Adding..." : `Add Selected (${selectedPresets.size})`}
                </button>
              )}
            </div>
            {CATEGORIES.map((cat) => (
              <div key={cat} className="preset-category">
                <span className="preset-category-label">{cat}</span>
                <div className="preset-grid">
                  {DEFAULT_SEEDS.filter((d) => d.category === cat).map((d) => {
                    const key = `${d.provider}:${d.token}`;
                    const added = seedUrls.has(getBoardUrl(d));
                    return (
                      <label key={key} className={`preset-label${added ? " added" : ""}`}>
                        <input
                          type="checkbox"
                          checked={added || selectedPresets.has(key)}
                          disabled={added}
                          onChange={() => togglePreset(key)}
                        />
                        {d.company}
                        {added && <span className="preset-added-tag">added</span>}
                      </label>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {error && <div className="error-banner">{error}</div>}

      {/* Stats */}
      {result && (
        <div className="stats-bar">
          <span>Track: <strong>{result.track}</strong></span>
          <span>Posted within: <strong>{result.posted_within}</strong></span>
          <span>Fetched: <strong>{(result.stats as any).total_fetched ?? 0}</strong></span>
          <span>Matched: <strong>{(result.stats as any).matched_track ?? 0}</strong></span>
          <span>New: <strong>{(result.stats as any).stored ?? 0}</strong></span>
          <span>Dupes skipped: <strong>{(result.stats as any).skipped_dupes ?? 0}</strong></span>
        </div>
      )}

      {/* Results table */}
      {filteredJobs.length > 0 ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th className="sortable" onClick={() => toggleSort("company")}>Company{sortIndicator("company")}</th>
                <th className="sortable" onClick={() => toggleSort("title")}>Role{sortIndicator("title")}</th>
                <th className="sortable" onClick={() => toggleSort("location")}>Location{sortIndicator("location")}</th>
                <th className="sortable" onClick={() => toggleSort("posted_age_hours")}>Posted{sortIndicator("posted_age_hours")}</th>
                <th>Level</th>
                <th>YOE</th>
                <th>Apply Link</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredJobs.map((job) => {
                const isExpanded = expandedJob === job.id;
                const jdText = job.jd_raw_text || "";
                const previewText = jdText.length > 500 ? jdText.slice(0, 500) + "..." : jdText;
                return (
                  <React.Fragment key={job.id}>
                    <tr className={isExpanded ? "row-expanded" : ""}>
                      <td>{job.company}</td>
                      <td>
                        <a
                          href="#"
                          onClick={(e) => {
                            e.preventDefault();
                            setExpandedJob(isExpanded ? null : job.id);
                          }}
                          className={isExpanded ? "role-link-active" : ""}
                        >
                          {job.title}
                        </a>
                      </td>
                      <td>{job.location || "—"}</td>
                      <td>{formatAge(job.posted_age_hours)}</td>
                      <td>
                        <span className={`badge badge-level-${job.experience_level || "entry-level"}`}>
                          {job.experience_level || "entry-level"}
                        </span>
                      </td>
                      <td>{job.yoe_min !== null ? `${job.yoe_min}+` : "—"}</td>
                      <td>
                        {job.apply_url ? (
                          <a href={job.apply_url} target="_blank" rel="noopener noreferrer">
                            Apply <span className={`badge badge-${job.apply_url_status}`}>{job.apply_url_status}</span>
                          </a>
                        ) : (
                          <span className="badge badge-unknown">unknown</span>
                        )}
                      </td>
                      <td>
                        <div style={{ display: "flex", gap: "0.3rem" }}>
                          {job.apply_url && (
                            <button
                              className="btn-secondary btn-sm"
                              onClick={() => copyLink(job.apply_url!)}
                              title="Copy apply link"
                            >
                              Copy
                            </button>
                          )}
                          <button
                            className="btn-secondary btn-sm"
                            onClick={() => addToQueue(job.id)}
                            title="Add to queue"
                          >
                            + Queue
                          </button>
                        </div>
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr className="jd-preview-row">
                        <td colSpan={8}>
                          <div className="jd-preview-content">
                            <div className="jd-preview-meta">
                              <span>{job.company}</span>
                              <span>{job.location || "No location"}</span>
                              <span>{job.platform}</span>
                              <span className={`badge badge-level-${job.experience_level || "entry-level"}`}>
                                {job.experience_level || "entry-level"}
                              </span>
                              {job.yoe_min !== null && <span>{job.yoe_min}+ yrs exp</span>}
                              <span>{formatAge(job.posted_age_hours)}</span>
                            </div>
                            {previewText ? (
                              <div className="jd-preview-text">{previewText}</div>
                            ) : (
                              <p style={{ color: "#8b949e", fontSize: "0.85rem" }}>No job description available.</p>
                            )}
                            <div className="jd-preview-actions">
                              <button
                                className="btn-secondary btn-sm"
                                onClick={() => setDetail(job)}
                              >
                                Full Details
                              </button>
                              {job.apply_url && (
                                <a
                                  href={job.apply_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="btn-primary btn-sm"
                                  style={{ textDecoration: "none" }}
                                >
                                  Apply
                                </a>
                              )}
                              <button
                                className="btn-secondary btn-sm"
                                onClick={() => addToQueue(job.id)}
                              >
                                + Queue
                              </button>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        !loading && (
          result ? (
            jobs.length > 0 && (locationFilter !== "All" || levelFilter !== "All") ? (
              <div className="empty">
                <p>No jobs match the current filters. Try setting Location and Level to "All" to see all {jobs.length} results.</p>
              </div>
            ) : null
          ) : (
            <div className="empty">
              <p>
                {hasSeeds
                  ? "Click Run Search to find jobs from your seeds."
                  : "Add at least one seed to get started."}
              </p>
            </div>
          )
        )
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
            {detail.evidence.length > 0 && (
              <div className="detail-evidence">
                <h4 style={{ fontSize: "0.85rem", marginBottom: "0.5rem" }}>Evidence Flags</h4>
                {detail.evidence.map((ev, i) => (
                  <div key={i} className="evidence-item">
                    <strong>{ev.type}:</strong> {ev.text}
                  </div>
                ))}
              </div>
            )}
            <p style={{ marginTop: "1rem", fontSize: "0.75rem", color: "#8b949e" }}>
              Source: <a href={detail.source_url} target="_blank" rel="noopener noreferrer">{detail.source_url}</a>
              <br />
              Scraped: {detail.scrape_ts}
            </p>
          </div>
        </>
      )}
    </div>
  );
}
