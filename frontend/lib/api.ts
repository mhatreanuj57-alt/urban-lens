/** UrbanLens API client — typed fetch wrapper with auth token handling. */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";
const TOKEN_KEY = "urbanlens.token";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  const hasContentType = Object.keys(headers).some(
    (k) => k.toLowerCase() === "content-type",
  );
  if (!hasContentType && !(options.body instanceof FormData) && options.body) {
    headers["Content-Type"] = "application/json";
  }
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch {
    throw new ApiError(0, "Cannot reach the UrbanLens server. Is the API running?");
  }

  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) {
        detail = body.detail
          .map((d: { msg?: string; loc?: string[] }) => d.msg ?? JSON.stringify(d))
          .join("; ");
      }
    } catch {
      /* keep default detail */
    }
    if (res.status === 401 && typeof window !== "undefined") {
      setToken(null);
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type IssueType =
  | "pothole"
  | "garbage"
  | "damaged_streetlight"
  | "waterlogging"
  | "illegal_dumping";

export const ISSUE_LABELS: Record<IssueType, string> = {
  pothole: "Pothole",
  garbage: "Garbage",
  damaged_streetlight: "Damaged Streetlight",
  waterlogging: "Waterlogging",
  illegal_dumping: "Illegal Dumping",
};

export const STATUS_LABELS: Record<string, string> = {
  submitted: "Submitted",
  under_review: "Under Review",
  verified: "Verified",
  assigned: "Assigned",
  in_progress: "In Progress",
  resolved: "Resolved",
  rejected: "Rejected",
  open: "Open",
  closed: "Closed",
};

export const STATUS_STYLES: Record<string, string> = {
  submitted: "bg-ink-100 text-ink-700",
  under_review: "bg-amber-100 text-amber-800",
  verified: "bg-blue-100 text-blue-800",
  assigned: "bg-indigo-100 text-indigo-800",
  in_progress: "bg-purple-100 text-purple-800",
  resolved: "bg-green-100 text-green-800",
  closed: "bg-ink-200 text-ink-600",
  rejected: "bg-red-100 text-red-700",
  open: "bg-sky-100 text-sky-800",
};

export interface User {
  id: string;
  email: string;
  display_name: string | null;
  role: "citizen" | "moderator" | "admin";
  is_active: boolean;
  consent_training: boolean;
  created_at: string;
}

export interface MediaAsset {
  id: string;
  kind: string;
  object_key: string;
  public_object_key: string | null;
  public_url?: string | null;
  mime_type: string;
  width: number | null;
  height: number | null;
  captured_at: string | null;
  created_at: string;
}

export interface InferenceRun {
  id: string;
  task: "detection" | "embedding" | "blur" | "risk";
  model_name: string;
  model_version: string;
  result: {
    detections?: Detection[];
    needs_review?: boolean;
    status?: string;
    embedding?: number[];
    dim?: number;
    faces_blurred?: number;
  };
  latency_ms: number | null;
  created_at: string;
}

export interface Detection {
  bbox: [number, number, number, number];
  class_name: string;
  confidence: number;
}

export interface PriorityFactors {
  severity: number;
  confirmations: number;
  recency: number;
  risk_context: number;
  road_context: number;
  weights: Record<string, number>;
}

export interface Report {
  id: string;
  reporter_id: string;
  incident_id: string | null;
  issue_type: IssueType | null;
  status: string;
  description: string | null;
  landmark: string | null;
  location_source: string;
  latitude: number | null;
  longitude: number | null;
  public_latitude: number | null;
  public_longitude: number | null;
  consent_location: boolean;
  occurred_at: string | null;
  submitted_at: string;
  priority_score: number | null;
  priority_factors: PriorityFactors | null;
  severity_score: number | null;
  verification_state: string;
}

export interface ReportDetail extends Report {
  media_assets: MediaAsset[];
  inference_runs: InferenceRun[];
}

export interface Incident {
  id: string;
  primary_issue_type: IssueType;
  lifecycle_status: string;
  latitude: number | null;
  longitude: number | null;
  ward_id: string | null;
  severity_score: number | null;
  priority_score: number | null;
  priority_factors: PriorityFactors | null;
  report_count: number;
  first_seen_at: string;
  last_seen_at: string;
  resolved_at: string | null;
  reports?: Report[];
}

export interface AuditEvent {
  id: string;
  actor_id: string | null;
  entity_type: string;
  entity_id: string;
  action: string;
  previous_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  created_at: string;
}

export interface ComplaintDraft {
  report_id: string;
  language: string;
  subject: string;
  body: string;
}

export interface Hotspot {
  latitude: number;
  longitude: number;
  report_count: number;
  top_issue_type: string | null;
  avg_priority: number | null;
}

export interface SummaryStats {
  total_reports: number;
  reports_by_status: Record<string, number>;
  reports_by_issue: Record<string, number>;
  total_incidents: number;
  open_incidents: number;
  resolved_incidents: number;
}

export interface RiskCell {
  grid_cell: string;
  latitude: number;
  longitude: number;
  risk_level: "low" | "medium" | "high";
  risk_score: number;
  rainfall_mm_24h: number;
  verified_waterlogging_30d: number;
}

export interface SignResponse {
  object_key: string;
  upload_url: string;
  method: string;
  expires_in: number;
  headers: Record<string, string>;
}

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

function qs(params?: Record<string, string | number | boolean | undefined>) {
  if (!params) return "";
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "") sp.set(k, String(v));
  });
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export const authApi = {
  register: (data: { email: string; password: string; display_name?: string; consent_training?: boolean }) =>
    apiFetch<User>("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (email: string, password: string) => {
    const form = new URLSearchParams({ username: email, password });
    return apiFetch<Token>("/auth/token", {
      method: "POST",
      body: form.toString(),
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },
  me: () => apiFetch<User>("/auth/me"),
};

interface Token {
  access_token: string;
  token_type: string;
}

export const reportsApi = {
  list: (params?: { issue_type?: IssueType; status?: string; mine?: boolean; limit?: number; offset?: number }) =>
    apiFetch<Report[]>(`/reports/${qs(params)}`),
  get: (id: string) => apiFetch<ReportDetail>(`/reports/${id}`),
  create: (data: {
    issue_type: IssueType;
    description?: string;
    latitude: number;
    longitude: number;
    location_source?: string;
    landmark?: string;
    occurred_at?: string | null;
    consent_location: boolean;
    consent_training: boolean;
    media: { object_key: string; mime_type: string; kind: "image" | "video" }[];
  }) => apiFetch<ReportDetail>("/reports/", { method: "POST", body: JSON.stringify(data) }),
  verify: (id: string, decision: "verified" | "rejected", reason?: string) =>
    apiFetch<ReportDetail>(`/reports/${id}/verify`, {
      method: "POST",
      body: JSON.stringify({ decision, reason }),
    }),
  complaint: (id: string, language: "en" | "hi" | "mr") =>
    apiFetch<ComplaintDraft>(`/reports/${id}/complaint`, {
      method: "POST",
      body: JSON.stringify({ language }),
    }),
};

export const incidentsApi = {
  list: (params?: { issue_type?: IssueType; status?: string; limit?: number; offset?: number }) =>
    apiFetch<Incident[]>(`/incidents/${qs(params)}`),
  get: (id: string) => apiFetch<Incident>(`/incidents/${id}`),
  history: (id: string) => apiFetch<AuditEvent[]>(`/incidents/${id}/history`),
  updateStatus: (id: string, lifecycle_status: string, note?: string) =>
    apiFetch<Incident>(`/incidents/${id}/status`, {
      method: "POST",
      body: JSON.stringify({ lifecycle_status, note }),
    }),
};

export const uploadsApi = {
  sign: (filename: string, content_type: string, size_bytes: number) =>
    apiFetch<SignResponse>(
      `/uploads/sign${qs({ filename, content_type, size_bytes })}`,
      { method: "POST" },
    ),
  upload: async (sign: SignResponse, file: File) => {
    const res = await fetch(sign.upload_url, {
      method: sign.method,
      headers: sign.headers,
      body: file,
    });
    if (!res.ok) throw new ApiError(res.status, `Upload failed (${res.status})`);
  },
};

export const analyticsApi = {
  hotspots: (days = 30) => apiFetch<Hotspot[]>(`/analytics/hotspots?days=${days}`),
  summary: () => apiFetch<SummaryStats>("/analytics/summary"),
};

export const riskApi = {
  waterlogging: (lat: number, lng: number) =>
    apiFetch<RiskCell>(`/risk/waterlogging?lat=${lat}&lng=${lng}`),
};
