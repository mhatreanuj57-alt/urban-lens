"use client";

import { useEffect, useState } from "react";
import { reportsApi, type Report } from "@/lib/api";

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    reportsApi
      .list()
      .then(setReports)
      .catch(() => setReports([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading reports...</p>;

  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold mb-4">Reports</h1>
      {reports.length === 0 ? (
        <p className="text-gray-500">No reports yet.</p>
      ) : (
        <ul className="space-y-2">
          {reports.map((r) => (
            <li key={r.id} className="border rounded p-3">
              <span className="font-medium">{r.issue_type || "Unknown"}</span>
              <span className="ml-2 text-sm text-gray-500">{r.status}</span>
              {r.description && <p className="text-sm mt-1">{r.description}</p>}
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
