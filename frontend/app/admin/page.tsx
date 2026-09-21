"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  analyticsApi,
  incidentsApi,
  reportsApi,
  ISSUE_LABELS,
  ApiError,
  type Incident,
  type Report,
  type SummaryStats,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import StatusBadge from "@/components/ui/StatusBadge";
import Button from "@/components/ui/Button";
import { Loading, ErrorState, EmptyState } from "@/components/ui/States";

const LIFECYCLE = ["open", "assigned", "in_progress", "resolved", "closed"];

function Summary({ stats }: { stats: SummaryStats }) {
  const cards: [string, number | string][] = [
    ["Reports", stats.total_reports],
    ["Incidents", stats.total_incidents],
    ["Open incidents", stats.open_incidents],
    ["Resolved", stats.resolved_incidents],
  ];
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {cards.map(([label, value]) => (
        <div key={label} className="card p-4">
          <p className="text-sm text-ink-500">{label}</p>
          <p className="mt-1 text-2xl font-bold text-ink-900">{value}</p>
        </div>
      ))}
    </div>
  );
}

function VerificationQueue({ onReviewed }: { onReviewed: () => void }) {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const all = await reportsApi.list({ status: "submitted", limit: 20 });
      setReports(all.filter((r) => r.verification_state === "unreviewed"));
    } catch {
      setReports([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function decide(r: Report, decision: "verified" | "rejected") {
    setBusyId(r.id);
    try {
      await reportsApi.verify(r.id, decision);
      setReports((prev) => prev.filter((x) => x.id !== r.id));
      onReviewed();
    } catch {
      /* keep in queue */
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="card p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-500">Verification queue</h2>
      {loading ? (
        <Loading label="Loading queue…" />
      ) : reports.length === 0 ? (
        <p className="mt-3 text-sm text-ink-500">Nothing waiting for review.</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {reports.map((r) => (
            <li key={r.id} className="flex items-center justify-between gap-3 rounded-lg bg-ink-50 px-3 py-2">
              <div className="min-w-0">
                <Link href={`/reports/${r.id}`} className="truncate font-medium text-ink-900 hover:underline">
                  {r.issue_type ? ISSUE_LABELS[r.issue_type] : "Report"}
                </Link>
                <p className="truncate text-xs text-ink-500">{r.description || r.landmark || "—"}</p>
              </div>
              <div className="flex shrink-0 gap-2">
                <Button onClick={() => decide(r, "verified")} loading={busyId === r.id}>Verify</Button>
                <Button variant="secondary" onClick={() => decide(r, "rejected")} disabled={busyId === r.id}>Reject</Button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function IncidentWorkflow({ incidents, onChange }: { incidents: Incident[]; onChange: () => void }) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function update(id: string, status: string) {
    setBusyId(id);
    setError(null);
    try {
      await incidentsApi.updateStatus(id, status);
      onChange();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Update failed.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="card p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-500">Incident workflow</h2>
      {error && <p className="field-error">{error}</p>}
      {incidents.length === 0 ? (
        <p className="mt-3 text-sm text-ink-500">No incidents yet.</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {incidents.map((i) => (
            <li key={i.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-ink-50 px-3 py-2">
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-ink-900">
                  {ISSUE_LABELS[i.primary_issue_type] ?? i.primary_issue_type}
                  <span className="ml-2 text-xs font-normal text-ink-500">{i.report_count} reports</span>
                </p>
                <StatusBadge status={i.lifecycle_status} className="mt-1" />
              </div>
              <select
                value={i.lifecycle_status}
                disabled={busyId === i.id}
                onChange={(e) => update(i.id, e.target.value)}
                className="input w-auto capitalize"
                aria-label="Update incident status"
              >
                {LIFECYCLE.map((s) => (
                  <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
                ))}
              </select>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function AdminPage() {
  const { user, loading: authLoading, isModerator } = useAuth();
  const [stats, setStats] = useState<SummaryStats | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, inc] = await Promise.all([
        analyticsApi.summary(),
        incidentsApi.list({ limit: 20 }),
      ]);
      setStats(s);
      setIncidents(inc);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load the dashboard.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!authLoading && isModerator) load();
  }, [authLoading, isModerator, load, tick]);

  if (authLoading) return <div className="container-page py-10"><Loading /></div>;

  if (!isModerator) {
    return (
      <div className="container-page py-10">
        <EmptyState
          title="Moderators only"
          message={user ? "Your account does not have dashboard access." : "Sign in with a moderator or admin account."}
          action={<Link href="/login"><Button>Sign in</Button></Link>}
        />
      </div>
    );
  }

  return (
    <div className="container-page space-y-5 py-8">
      <h1 className="text-2xl font-bold text-ink-900">Operations dashboard</h1>
      {loading ? (
        <Loading label="Loading dashboard…" />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : (
        <>
          {stats && <Summary stats={stats} />}
          <VerificationQueue onReviewed={() => setTick((t) => t + 1)} />
          <IncidentWorkflow incidents={incidents} onChange={() => setTick((t) => t + 1)} />
        </>
      )}
    </div>
  );
}
