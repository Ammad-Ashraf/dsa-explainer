// The local API (backend/dsa_explainer/api/app.py). Types mirror its JSON replies.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export type Level = "beginner" | "intermediate" | "advanced";
export type Quality = "draft" | "standard" | "high";
export const LEVELS: Level[] = ["beginner", "intermediate", "advanced"];
export const QUALITY_LABELS: Record<Quality, string> = { draft: "Draft · 480p", standard: "Standard · 720p", high: "High · 1080p" };

export interface Health {
  ok: boolean;
  version: string;
  llm: { configured: boolean; provider: string | null; provider_name?: string; model: string | null; local?: boolean };
  voice: { ready: boolean; voice: string };
  busy: boolean;
}

export interface AlgorithmInfo {
  id: string;
  title: string;
  category: string;
  category_title: string;
  difficulty: Level;
  summary: string;
  description: string;
  complexity: { best: string; average: string; worst: string; space: string };
  pseudocode: string[];
  requires: string;
  presets: Record<string, unknown>;
  operations: Record<string, string[]>;
  facts: string[];
  /** facts the video shows beside the picture after every step */
  strip: string[];
  /** operation -> the pseudocode lines it runs (the video highlights them) */
  op_lines: Record<string, number[]>;
  view: string;
  noun: string;
}
export interface Catalog { categories: Record<string, string>; algorithms: AlgorithmInfo[] }

export interface PlanSummary { id: string; title: string; topic: string; structure: string; level: Level; steps: number; questions: number }

export interface StageState { status: "running" | "done" | "failed" | "skipped"; detail?: string; seconds?: number }
export interface Job {
  id: string;
  kind: "create" | "render" | "revise";
  params: Record<string, unknown>;
  status: "queued" | "running" | "done" | "failed" | "cancelled";
  result: { lesson_id: string; version: number; changed?: string[] } | null;
  error: string | null;
  stages: Record<string, StageState>;
  fraction: number;
  message: string;
}

export interface Chapter { name: string; kind: string; start: number; seconds: number }
export interface VersionInfo {
  version: number;
  video: string;
  created?: string;
  quality?: Quality;
  seconds?: number;
  clips?: number;
  rendered?: string[];
  reused?: number;
  chapters?: Chapter[];
  checks?: number;
  rejected?: string[];
  request?: string | null;
  changed?: string[];
  timings?: Record<string, number>;
}
export interface LessonSummary {
  id: string; title: string; topic: string; structure: string; level: Level; created: string; source: string;
  versions: number; latest_version: number | null; seconds: number | null;
}
export interface SceneView { label: string; kind: string; caption: string; narration: string; op: string | null; speed: number; points: string[] }
export interface QuizQuestion { question: string; options: string[]; answer: number; explanation: string }
export interface LessonView {
  scenes: SceneView[];
  quiz: QuizQuestion[];
  verified: { ok: boolean; checks: number; errors: string[] };
  plan: Record<string, unknown>;
}
export interface LessonDetail extends LessonView {
  id: string; title: string; topic: string; structure: string; level: Level; created: string; source: string;
  versions: VersionInfo[]; version: number; version_info: VersionInfo; video_url: string;
}
export interface PlanDetail extends PlanSummary, LessonView {}

export interface Provider {
  id: string; name: string; base_url: string; default_model: string; fallback_model: string; key_url: string;
  needs_key: boolean; local: boolean; structured: string; notes: string; ready: boolean;
  saved: { model: string; fallback_model: string; base_url: string; key_set: boolean; key_hint: string };
}
export interface Providers {
  active: string | null;
  env: { base_url: string; model: string; fallback_model: string; key_hint: string } | null;
  providers: Provider[];
  in_use: Health["llm"];
}
export interface Preferences { default_quality: Quality; voice: string; render_workers: number }
export interface SettingsReply { preferences: Preferences; qualities: Quality[] }

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch {
      /* not JSON */
    }
    throw new ApiError(detail || `Request failed (${response.status})`, response.status);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
const post = <T,>(path: string, body?: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(body ?? {}) });
const put = <T,>(path: string, body: unknown) => request<T>(path, { method: "PUT", body: JSON.stringify(body) });

export const api = {
  health: () => request<Health>("/api/health"),
  catalog: () => request<Catalog>("/api/catalog"),
  plans: () => request<PlanSummary[]>("/api/plans"),
  plan: (id: string) => request<PlanDetail>(`/api/plans/${id}`),
  renderPlan: (id: string, quality?: Quality) => post<Job>(`/api/plans/${id}/render`, { quality }),
  createLesson: (topic: string, level: Level, quality?: Quality) => post<Job>("/api/lessons", { topic, level, quality }),
  lessons: () => request<LessonSummary[]>("/api/lessons"),
  lesson: (id: string, version?: number) => request<LessonDetail>(`/api/lessons/${id}${version ? `?version=${version}` : ""}`),
  deleteLesson: (id: string) => request<void>(`/api/lessons/${id}`, { method: "DELETE" }),
  revise: (id: string, requestText: string, version?: number, quality?: Quality) =>
    post<Job>(`/api/lessons/${id}/revisions`, { request: requestText, version, quality }),
  job: (id: string) => request<Job>(`/api/jobs/${id}`),
  cancelJob: (id: string) => post<Job>(`/api/jobs/${id}/cancel`),
  settings: () => request<SettingsReply>("/api/settings"),
  saveSettings: (preferences: Partial<Preferences>) => put<SettingsReply>("/api/settings", { preferences }),
  providers: () => request<Providers>("/api/providers"),
  saveProvider: (id: string, body: Partial<{ api_key: string; model: string; fallback_model: string; base_url: string; activate: boolean }>) =>
    put<Providers>(`/api/providers/${id}`, body),
  activateProvider: (provider: string | null) => post<Providers>("/api/providers/active", { provider }),
  testProvider: (id: string, body: Partial<{ api_key: string; model: string; base_url: string }>) =>
    post<{ ok: boolean; model?: string; seconds?: number; reply?: string; error?: string }>(`/api/providers/${id}/test`, body),
  models: (id: string) => request<{ models: string[] }>(`/api/providers/${id}/models`),
};

// ---- hooks -------------------------------------------------------------------------

export const useHealth = () => useQuery({ queryKey: ["health"], queryFn: api.health, refetchInterval: 15000 });
export const useCatalog = () => useQuery({ queryKey: ["catalog"], queryFn: api.catalog, staleTime: Infinity });
export const usePlans = () => useQuery({ queryKey: ["plans"], queryFn: api.plans, staleTime: Infinity });
export const useLessons = () => useQuery({ queryKey: ["lessons"], queryFn: api.lessons });
export const useLesson = (id: string | undefined, version?: number) =>
  useQuery({ queryKey: ["lesson", id, version ?? "latest"], queryFn: () => api.lesson(id!, version), enabled: !!id });
export const useProviders = () => useQuery({ queryKey: ["providers"], queryFn: api.providers });
export const useSettings = () => useQuery({ queryKey: ["settings"], queryFn: api.settings });

export function useInvalidate() {
  const client = useQueryClient();
  return (...keys: string[]) => keys.forEach((key) => client.invalidateQueries({ queryKey: [key] }));
}

export function useDeleteLesson() {
  const invalidate = useInvalidate();
  return useMutation({ mutationFn: api.deleteLesson, onSuccess: () => invalidate("lessons") });
}

// ---- helpers ------------------------------------------------------------------------

export function algorithmById(catalog: Catalog | undefined, id: string | undefined): AlgorithmInfo | undefined {
  if (!catalog || !id) return undefined;
  const key = id === "graph" ? "bfs" : id;
  return catalog.algorithms.find((a) => a.id === key);
}

export function formatSeconds(seconds: number | null | undefined): string {
  if (seconds == null) return "–";
  const s = Math.round(seconds);
  return s < 60 ? `${s} s` : `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, "0")} s`;
}

export function formatDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function presetTopic(algo: AlgorithmInfo, presetName: string, data: unknown): string {
  return `Explain ${algo.title.toLowerCase()} step by step on this data (${presetName}): ${JSON.stringify(data)}`;
}
