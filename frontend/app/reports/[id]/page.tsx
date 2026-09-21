"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ISSUE_LABELS,
  reportsApi,
  ApiError,
  type ComplaintDraft,
  type Detection,
  type ReportDetail,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import StatusBadge from "@/components/ui/StatusBadge";
import Button from "@/components/ui/Button";
import { Loading, ErrorState } from "@/components/ui/States";

function PriorityBreakdown({ report }: { report: ReportDetail }) {
  const f = report.priority_factors;
  if (report.priority_score == null || !f) return null;
  const rows: [string, number][] = [
    ["Severity", f.severity],
    ["Confirmations", f.confirmations],
    ["Recency", f.recency],
    ["Risk context", f.risk_context],
    ["Road context", f.road_context],
  ];
  return (
    <section className="card p-5">
      <div className="flex items-baseline justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-500">Priority</h2>
        <span className="text-2xl font-bold text-ink-900">{report.priority_score.toFixed(0)}</span>
      </div>
      <ul className="mt-3 space-y-2">
        {rows.map(([label, value]) => (
          <li key={label} className="flex items-center gap-3 text-sm">
            <span className="w-28 shrink-0 text-ink-600">{label}</span>
            <span className="h-2 flex-1 overflow-hidden rounded-full bg-ink-100">
              <span
                className="block h-full rounded-full bg-primary-500"
                style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
              />
            </span>
            <span className="w-8 shrink-0 text-right tabular-nums text-ink-700">{value.toFixed(0)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function AiAnalysis({ report }: { report: ReportDetail }) {
  const detectionRuns = report.inference_runs.filter((r) => r.task === "detection");
  const detections: Detection[] = detectionRuns.flatMap((r) => r.result.detections ?? []);
  const needsReview = detectionRuns.some((r) => r.result.needs_review);

  return (
    <section className="card p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-500">AI analysis</h2>
      {detections.length === 0 ? (
        <p className="mt-2 text-sm text-ink-500">
          No detection results yet — analysis runs in the background after upload.
        </p>
      ) : (
        <>
          {needsReview && (
            <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
              Low confidence — a reviewer should confirm these labels.
            </p>
          )}
          <ul className="mt-3 space-y-2">
            {detections.map((d, i) => (
              <li key={i} className="flex items-center justify-between rounded-lg bg-ink-50 px-3 py-2 text-sm">
                <span className="font-medium capitalize text-ink-800">{d.class_name.replace(/_/g, " ")}</span>
                <span className="tabular-nums text-ink-500">{(d.confidence * 100).toFixed(0)}% confidence</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function ReportMedia({ report }: { report: ReportDetail }) {
  const base =
    process.env.NEXT_PUBLIC_STORAGE_URL ||
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/v1\/?$/, "").replace(/\/$/, "") ||
    "http://localhost:9000";
  return (
    <section className="card p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-500">Evidence</h2>
      <div className="mt-3 grid grid-cols-2 gap-3">
        {report.media_assets.map((m) =>
          m.public_object_key ? (
            <figure key={m.id}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`${base}/urbanlens-public/${m.public_object_key}`}
                alt={report.issue_type ? ISSUE_LABELS[report.issue_type] : "Reported issue"}
                className="w-full rounded-lg border border-ink-200 object-cover"
              />
              <figcaption className="mt-1 text-xs text-ink-400">
                Face-blurred public copy
              </figcaption>
            </figure>
          ) : (
            <p key={m.id} className="text-sm text-ink-500">
              Media is still being processed before it can be shown.
            </p>
          ),
        )}
      </div>
    </section>
  );
}

function ComplaintExport({ reportId }: { reportId: string }) {
  const [lang, setLang] = useState<"en" | "hi" | "mr">("en");
  const [draft, setDraft] = useState<ComplaintDraft | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      setDraft(await reportsApi.complaint(reportId, lang));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not generate a draft.");
    } finally {
      setBusy(false);
    }
  }

  async function copy() {
    if (!draft) return;
    await navigator.clipboard.writeText(`${draft.subject}\n\n${draft.body}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <section className="card p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-500">Complaint draft</h2>
      <div className="mt-3 flex items-center gap-2">
        <select value={lang} onChange={(e) => setLang(e.target.value as "en" | "hi" | "mr")} className="input max-w-[160px]">
          <option value="en">English</option>
          <option value="hi">हिन्दी</option>
          <option value="mr">मराठी</option>
        </select>
        <Button onClick={generate} loading={busy}>{draft ? "Regenerate" : "Generate"}</Button>
      </div>
      {error && <p className="field-error">{error}</p>}
      {draft && (
        <div className="mt-4 space-y-2">
          <input readOnly value={draft.subject} className="input font-medium" />
          <textarea readOnly rows={8} value={draft.body} className="input whitespace-pre-wrap" />
          <Button variant="secondary" onClick={copy}>{copied ? "Copied!" : "Copy complaint"}</Button>
          <p className="text-xs text-ink-400">Factual draft from confirmed data — review and edit before sending.</p>
        </div>
      )}
    </section>
  );
}

function VerifyPanel({ report, onDone }: { report: ReportDetail; onDone: () => void }) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState<"verified" | "rejected" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function decide(decision: "verified" | "rejected") {
    setBusy(decision);
    setError(null);
    try {
      await reportsApi.verify(report.id, decision, reason.trim() || undefined);
      onDone();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Action failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="card border-primary-200 bg-primary-50/40 p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-500">Moderator</h2>
      <p className="mt-1 text-sm text-ink-600">Current state: <b className="capitalize">{report.verification_state}</b></p>
      {report.verification_state !== "unreviewed" ? (
        <p className="mt-2 text-sm text-ink-500">This report has already been reviewed.</p>
      ) : (
        <div className="mt-3 space-y-3">
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={2}
            className="input"
            placeholder="Reason / note (optional)"
            maxLength={1000}
          />
          {error && <p className="field-error">{error}</p>}
          <div className="flex gap-2">
            <Button onClick={() => decide("verified")} loading={busy === "verified"}>Verify</Button>
            <Button variant="danger" onClick={() => decide("rejected")} loading={busy === "rejected"}>Reject</Button>
          </div>
        </div>
      )}
    </section>
  );
}

export default function ReportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { isModerator, loading: authLoading } = useAuth();
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    setError(null);
    try {
      setReport(await reportsApi.get(id));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load this report.");
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (error && !report) return <div className="container-page py-10"><ErrorState message={error} onRetry={load} /></div>;
  if (!report) return <div className="container-page py-10"><Loading label="Loading report…" /></div>;

  return (
    <div className="container-page max-w-3xl space-y-6 py-10">
      <div className="flex items-center justify-between">
        <Link href="/reports" className="text-sm text-primary-700 hover:underline">← My reports</Link>
        <StatusBadge status={report.status} />
      </div>

      <header className="card p-5">
        <h1 className="text-xl font-bold text-ink-900">
          {report.issue_type ? ISSUE_LABELS[report.issue_type] : "Report"}
        </h1>
        {report.description && <p className="mt-1 text-sm text-ink-600">{report.description}</p>}
        <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <div>
            <dt className="text-ink-400">Location</dt>
            <dd className="text-ink-700">
              {report.public_latitude != null && report.public_longitude != null
                ? `${report.public_latitude.toFixed(4)}, ${report.public_longitude.toFixed(4)}`
                : "—"}
              {report.landmark ? ` · ${report.landmark}` : ""}
            </dd>
          </div>
          <div>
            <dt className="text-ink-400">Submitted</dt>
            <dd className="text-ink-700">{new Date(report.submitted_at).toLocaleString()}</dd>
          </div>
        </dl>
      </header>

      {report.media_assets.length > 0 && <ReportMedia report={report} />}

      <AiAnalysis report={report} />
      <PriorityBreakdown report={report} />

      {!authLoading && isModerator && <VerifyPanel report={report} onDone={load} />}

      <ComplaintExport reportId={report.id} />
    </div>
  );
}
