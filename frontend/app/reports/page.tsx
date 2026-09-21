"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  reportsApi,
  ISSUE_LABELS,
  type Report,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import StatusBadge from "@/components/ui/StatusBadge";
import Button from "@/components/ui/Button";
import { Loading, ErrorState, EmptyState } from "@/components/ui/States";

export default function ReportsPage() {
  const { user, loading: authLoading } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setReports(await reportsApi.list({ mine: true }));
    } catch {
      setError("Could not load your reports.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!authLoading) load();
  }, [authLoading, load]);

  return (
    <div className="container-page py-8">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink-900">My reports</h1>
          <p className="text-sm text-ink-500">Track the issues you have submitted.</p>
        </div>
        <Link href="/reports/new"><Button>New report</Button></Link>
      </div>

      {authLoading || loading ? (
        <Loading label="Loading your reports…" />
      ) : !user ? (
        <div className="card px-6 py-10 text-center">
          <h2 className="text-lg font-semibold text-ink-800">Sign in to see your reports</h2>
          <div className="mt-4 flex justify-center gap-2">
            <Link href="/login"><Button>Sign in</Button></Link>
            <Link href="/register"><Button variant="secondary">Create account</Button></Link>
          </div>
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : reports.length === 0 ? (
        <EmptyState
          title="No reports yet"
          message="When you submit an issue it will appear here with its status."
          action={<Link href="/reports/new"><Button>Report an issue</Button></Link>}
        />
      ) : (
        <ul className="space-y-2">
          {reports.map((r) => (
            <li key={r.id}>
              <Link
                href={`/reports/${r.id}`}
                className="card flex items-center justify-between gap-3 p-4 transition hover:border-primary-300"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium text-ink-900">
                    {r.issue_type ? ISSUE_LABELS[r.issue_type] : "Report"}
                  </p>
                  <p className="truncate text-sm text-ink-500">
                    {r.description || (r.landmark ?? "No description")}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  {r.priority_score != null && (
                    <span className="text-sm tabular-nums text-ink-500">P{r.priority_score.toFixed(0)}</span>
                  )}
                  <StatusBadge status={r.status} />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
