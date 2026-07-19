const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function getToken(): string | null {
  return localStorage.getItem("datapilot_token");
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem("datapilot_token", token);
  else localStorage.removeItem("datapilot_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.body && !(options.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string>),
  };

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      /* response wasn't JSON — keep statusText */
    }
    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

// ---------- Types ----------

export interface User {
  id: string;
  email: string;
  full_name: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Project {
  id: string;
  name: string;
  created_at: string;
}

export interface Dataset {
  id: string;
  filename: string;
  domain: string | null;
  row_count: number | null;
  column_count: number | null;
  quality_score: number | null;
  created_at: string;
}

export interface ColumnProfile {
  column: string;
  dtype: string;
  missing_pct: number;
  duplicate_flagged: boolean;
  outlier_pct: number | null;
  unique_count: number;
}

export interface QualityReport {
  row_count: number;
  column_count: number;
  duplicate_row_pct: number;
  quality_score: number;
  columns: ColumnProfile[];
  warnings: string[];
}

export interface SkepticFlag {
  type: string;
  severity: "high" | "medium" | "low" | "info";
  message: string;
}

export interface Critique {
  flags: SkepticFlag[];
  trust_level: "high" | "medium" | "low";
}

export interface AskResponse {
  question: string;
  sql: string;
  result: Record<string, unknown>[];
  stat_test: Record<string, unknown> | null;
  explanation: string;
  critique: Critique;
  diff_summary: string | null;
  compared_insight_id: string | null;
  confidence_score: number;
}

export interface Insight {
  id: string;
  question: string;
  explanation: string | null;
  confidence_score: number | null;
  diff_summary: string | null;
  created_at: string;
}

export interface CleaningResult {
  cleaning_report: {
    rows_before: number;
    rows_after: number;
    duplicate_rows_removed: number;
    columns_flagged_for_manual_review: string[];
    actions: { column: string | null; action: string; [key: string]: unknown }[];
  };
  quality_score_before: number;
  quality_score_after: number;
}

export interface AutonomousAnalysis {
  correlations: {
    matrix: Record<string, Record<string, number>>;
    top_pairs: { column_a: string; column_b: string; correlation: number }[];
  };
  trends: { column: string; direction: string; slope_per_period: number; r_squared: number; periods_available: number }[];
  important_variables: string[];
  summary: string;
}

export interface ModelResult {
  task_type: string;
  target_column: string;
  class_labels: string[];
  n_train: number;
  n_test: number;
  baseline_model: { type: string; metrics: Record<string, number> };
  boosted_model: { type: string; metrics: Record<string, number> };
  chosen_model: string;
  feature_importance: { feature: string; importance: number }[];
}

export interface DashboardSpec {
  domain: string | null;
  kpi_cards: { label: string; value: number | string; unit?: string }[];
  missing_value_chart: { column: string; missing_pct: number }[];
  correlation_heatmap: Record<string, Record<string, number>>;
  histograms: Record<string, { bucket: string; count: number }[]>;
  bar_charts: Record<string, { category: string; count: number }[]>;
  time_series: { value_column: string; date_column: string; data: { period: string; value: number }[] } | null;
  trends: { column: string; direction: string; slope_per_period: number; r_squared: number; periods_available: number }[];
  feature_importance: { feature: string; importance: number }[] | null;
}

// ---------- API calls ----------

export const api = {
  register: (email: string, password: string, full_name?: string) =>
    request<AuthResponse>("/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>("/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  listProjects: () => request<Project[]>("/projects"),

  createProject: (name: string) =>
    request<Project>("/projects", { method: "POST", body: JSON.stringify({ name }) }),

  uploadDataset: (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<Dataset>(`/datasets/upload?project_id=${projectId}`, {
      method: "POST",
      body: formData,
    });
  },

  listDatasets: (projectId: string) => request<Dataset[]>(`/datasets?project_id=${projectId}`),

  getQualityReport: (datasetId: string) =>
    request<QualityReport>(`/datasets/${datasetId}/quality-report`),

  askAnalyst: (datasetId: string, question: string) =>
    request<AskResponse>(`/analyst/${datasetId}/ask`, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  getInsightHistory: (datasetId: string) =>
    request<Insight[]>(`/analyst/${datasetId}/history`),

  cleanDataset: (datasetId: string) =>
    request<CleaningResult>(`/datasets/${datasetId}/clean`, { method: "POST" }),

  getAnalysis: (datasetId: string) =>
    request<AutonomousAnalysis>(`/datasets/${datasetId}/analysis`),

  getDashboard: (datasetId: string) =>
    request<DashboardSpec>(`/datasets/${datasetId}/dashboard`),

  trainModel: (datasetId: string, targetColumn: string) =>
    request<ModelResult>(`/ml/${datasetId}/train?target_column=${encodeURIComponent(targetColumn)}`, {
      method: "POST",
    }),

  downloadCleanedCsv: async (datasetId: string) => {
    const token = localStorage.getItem("datapilot_token");
    const res = await fetch(`${API_BASE_URL}/datasets/${datasetId}/export/cleaned`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new ApiError("Failed to download cleaned dataset", res.status);
    return res.blob();
  },

  downloadPdfReport: async (datasetId: string) => {
    const token = localStorage.getItem("datapilot_token");
    const res = await fetch(`${API_BASE_URL}/datasets/${datasetId}/export/report`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new ApiError("Failed to generate report", res.status);
    return res.blob();
  },
};
