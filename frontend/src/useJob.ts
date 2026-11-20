// Follows a job through Server-Sent Events. The server replays every event from the start,
// then streams new ones; the browser reconnects by itself with Last-Event-ID if the line drops.
import { useEffect, useReducer } from "react";
import type { Job, StageState } from "./api";

export const STAGES = ["plan", "verify", "quiz", "voice", "draw", "join"] as const;
export type StageName = (typeof STAGES)[number];

export interface Rejection { stage: string; attempt: number; reason: string }
export interface Clip { index: number; key: string; name: string; seconds: number; cached: boolean }

export interface JobState {
  connected: boolean;
  status: Job["status"] | "connecting";
  stages: Partial<Record<StageName, StageState>>;
  message: string;
  fraction: number;
  rejected: Rejection[];
  scenes: { total: number; voiced: number; drawn: number; current?: string };
  clips: Record<number, Clip>;
  result: Job["result"];
  error: string | null;
}

const initial: JobState = {
  connected: false,
  status: "connecting",
  stages: {},
  message: "",
  fraction: 0,
  rejected: [],
  scenes: { total: 0, voiced: 0, drawn: 0 },
  clips: {},
  result: null,
  error: null,
};

type JobEvent = { type: string; seq: number; [key: string]: unknown };

function reduce(state: JobState, event: JobEvent | { type: "reset" } | { type: "open" }): JobState {
  switch (event.type) {
    case "reset":
      return initial;
    case "open":
      return { ...state, connected: true };
    case "job": {
      const e = event as unknown as { status: Job["status"]; result?: Job["result"]; error?: string | null };
      return { ...state, status: e.status, result: e.result ?? state.result, error: e.error ?? state.error };
    }
    case "stage": {
      const e = event as unknown as StageState & { stage: StageName };
      return { ...state, stages: { ...state.stages, [e.stage]: { status: e.status, detail: e.detail, seconds: e.seconds } } };
    }
    case "message": {
      const e = event as unknown as { text: string; fraction?: number | null };
      return { ...state, message: e.text, fraction: e.fraction != null ? Math.max(state.fraction, e.fraction) : state.fraction };
    }
    case "rejected": {
      const e = event as unknown as Rejection;
      return { ...state, rejected: [...state.rejected, { stage: e.stage, attempt: e.attempt, reason: e.reason }] };
    }
    case "scene": {
      const e = event as unknown as { stage: string; index: number; total: number; name: string };
      const scenes = { ...state.scenes, total: e.total, current: e.name };
      if (e.stage === "voice") scenes.voiced = Math.max(scenes.voiced, e.index + 1);
      else scenes.drawn = scenes.drawn + 1;
      return { ...state, scenes };
    }
    case "clip": {
      const e = event as unknown as Clip & { total: number };
      const clips = { ...state.clips, [e.index]: { index: e.index, key: e.key, name: e.name, seconds: e.seconds, cached: e.cached } };
      return { ...state, clips, scenes: { ...state.scenes, total: e.total } };
    }
    default:
      return state;
  }
}

export function useJob(jobId: string | undefined): JobState {
  const [state, dispatch] = useReducer(reduce, initial);
  useEffect(() => {
    if (!jobId) return;
    dispatch({ type: "reset" });
    const source = new EventSource(`/api/jobs/${jobId}/events`);
    const on = (e: MessageEvent) => dispatch(JSON.parse(e.data));
    const types = ["job", "stage", "message", "rejected", "scene", "clip"];
    types.forEach((t) => source.addEventListener(t, on as EventListener));
    source.addEventListener("open", () => dispatch({ type: "open" }));
    source.addEventListener("end", (e) => {
      const snapshot = JSON.parse((e as MessageEvent).data) as Job;
      dispatch({ type: "job", seq: -1, status: snapshot.status, result: snapshot.result, error: snapshot.error });
      source.close(); // the job is over: stop the browser from reconnecting
    });
    return () => source.close();
  }, [jobId]);
  return state;
}
