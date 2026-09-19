/** UrbanLens API base URL */
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";

/**
 * Fetch wrapper for UrbanLens API
 */
async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export interface Report {
  id: string;
  issue_type: string | null;
  status: string;
  description: string | null;
  submitted_at: string;
  priority_score: number | null;
  verification_state: string;
}

export interface Incident {
  id: string;
  primary_issue_type: string;
  lifecycle_status: string;
  severity_score: number | null;
  priority_score: number | null;
  report_count: number;
  first_seen_at: string;
  last_seen_at: string;
}

export const reportsApi = {
  list: (params?: { issue_type?: string; status?: string }) =>
    apiFetch<Report[]>(`/reports/?${new URLSearchParams(params as Record<string, string>)}`),
  get: (id: string) => apiFetch<Report>(`/reports/${id}`),
  create: (data: { issue_type?: string; description?: string }) =>
    apiFetch<Report>("/reports/", { method: "POST", body: JSON.stringify(data) }),
};

export const incidentsApi = {
  list: (params?: { issue_type?: string; status?: string }) =>
    apiFetch<Incident[]>(`/incidents/?${new URLSearchParams(params as Record<string, string>)}`),
  get: (id: string) => apiFetch<Incident>(`/incidents/${id}`),
};
