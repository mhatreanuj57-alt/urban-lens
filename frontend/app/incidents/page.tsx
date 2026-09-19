"use client";

import { useEffect, useState } from "react";
import { incidentsApi, type Incident } from "@/lib/api";

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    incidentsApi
      .list()
      .then(setIncidents)
      .catch(() => setIncidents([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading incidents...</p>;

  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold mb-4">Incidents</h1>
      {incidents.length === 0 ? (
        <p className="text-gray-500">No incidents yet.</p>
      ) : (
        <ul className="space-y-2">
          {incidents.map((i) => (
            <li key={i.id} className="border rounded p-3">
              <span className="font-medium">{i.primary_issue_type}</span>
              <span className="ml-2 text-sm text-gray-500">{i.lifecycle_status}</span>
              <span className="ml-2 text-sm text-gray-400">
                {i.report_count} reports
              </span>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
