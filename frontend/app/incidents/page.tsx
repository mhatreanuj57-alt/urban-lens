"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  incidentsApi,
  ISSUE_LABELS,
  type Incident,
  type IssueType,
} from "@/lib/api";
import MapView, { markerColor, type MapMarker } from "@/components/map/MapView";
import StatusBadge from "@/components/ui/StatusBadge";
import { Loading, ErrorState, EmptyState } from "@/components/ui/States";

const STATUS_OPTIONS = [
  "open", "assigned", "in_progress", "resolved", "closed",
];

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [issueType, setIssueType] = useState<IssueType | "">("");
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await incidentsApi.list({
        issue_type: issueType || undefined,
        status: status || undefined,
        limit: 200,
      });
      setIncidents(data);
    } catch {
      setError("Could not load incidents. Is the API running?");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [issueType, status]);

  const withCoords = useMemo(
    () => incidents.filter((i) => i.latitude != null && i.longitude != null),
    [incidents],
  );

  const markers: MapMarker[] = withCoords.map((i) => ({
    id: i.id,
    lat: i.latitude as number,
    lng: i.longitude as number,
    color: markerColor(i.primary_issue_type),
    label: ISSUE_LABELS[i.primary_issue_type] ?? i.primary_issue_type,
    onClick: () => setSelected(i.id),
  }));

  const sorted = useMemo(
    () =>
      [...withCoords].sort(
        (a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0),
      ),
    [withCoords],
  );

  return (
    <div className="container-page py-8">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-ink-900">Incidents map</h1>
          <p className="text-sm text-ink-500">Recurring issues clustered across Navi Mumbai.</p>
        </div>
        <div className="flex gap-2">
          <select
            value={issueType}
            onChange={(e) => setIssueType(e.target.value as IssueType | "")}
            className="input w-auto"
            aria-label="Filter by issue type"
          >
            <option value="">All issues</option>
            {(Object.keys(ISSUE_LABELS) as IssueType[]).map((t) => (
              <option key={t} value={t}>{ISSUE_LABELS[t]}</option>
            ))}
          </select>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="input w-auto"
            aria-label="Filter by status"
          >
            <option value="">All statuses</option>
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
            ))}
          </select>
        </div>
      </div>

      {error ? (
        <ErrorState message={error} onRetry={load} />
      ) : loading ? (
        <Loading label="Loading incidents…" />
      ) : incidents.length === 0 ? (
        <EmptyState title="No incidents" message="No reports match the current filters yet." />
      ) : (
        <div className="grid gap-5 lg:grid-cols-[1.6fr_1fr]">
          <MapView
            markers={markers}
            fitToMarkers
            className="h-[420px] w-full overflow-hidden rounded-xl border border-ink-200 lg:h-[620px]"
          />
          <div className="max-h-[620px] space-y-2 overflow-y-auto pr-1">
            {sorted.map((i) => (
              <button
                key={i.id}
                onClick={() => setSelected(i.id)}
                className={`card w-full p-4 text-left transition hover:border-primary-300 ${
                  selected === i.id ? "ring-2 ring-primary-300" : ""
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-2 font-medium text-ink-900">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: markerColor(i.primary_issue_type) }} />
                    {ISSUE_LABELS[i.primary_issue_type] ?? i.primary_issue_type}
                  </span>
                  <StatusBadge status={i.lifecycle_status} />
                </div>
                <div className="mt-2 flex items-center justify-between text-sm text-ink-500">
                  <span>{i.report_count} report{i.report_count === 1 ? "" : "s"}</span>
                  {i.priority_score != null && (
                    <span className="tabular-nums">priority {i.priority_score.toFixed(0)}</span>
                  )}
                </div>
                {i.reports && i.reports[0] && (
                  <Link
                    href={`/reports/${i.reports[0].id}`}
                    onClick={(e) => e.stopPropagation()}
                    className="mt-2 inline-block text-sm font-medium text-primary-700 hover:underline"
                  >
                    View report →
                  </Link>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
