"use client";

import { useEffect, useState } from "react";
import { incidentsApi, reportsApi, type Incident, type Report } from "@/lib/api";

export default function AdminPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([incidentsApi.list(), reportsApi.list()])
      .then(([inc, rep]) => {
        setIncidents(inc);
        setReports(rep);
      })
      .catch(() => {
        setIncidents([]);
        setReports([]);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading dashboard...</p>;

  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <section>
          <h2 className="text-lg font-semibold mb-2">Recent Reports</h2>
          {reports.length === 0 ? (
            <p className="text-gray-500">No reports</p>
          ) : (
            <ul className="space-y-1">
              {reports.slice(0, 5).map((r) => (
                <li key={r.id} className="text-sm border-b py-1">
                  {r.issue_type} — <span className="text-gray-500">{r.status}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
        <section>
          <h2 className="text-lg font-semibold mb-2">Active Incidents</h2>
          {incidents.length === 0 ? (
            <p className="text-gray-500">No incidents</p>
          ) : (
            <ul className="space-y-1">
              {incidents.slice(0, 5).map((i) => (
                <li key={i.id} className="text-sm border-b py-1">
                  {i.primary_issue_type} —{" "}
                  <span className="text-gray-500">{i.lifecycle_status}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}
