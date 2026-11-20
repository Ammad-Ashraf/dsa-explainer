import { useEffect, useState } from "react";
import { STAGES, type JobState, type StageName } from "../useJob";
import { Spinner } from "./ui";

const NAMES: Record<StageName, string> = { plan: "Plan", verify: "Verify", quiz: "Quiz", voice: "Voice", draw: "Draw", join: "Join" };
const WAITING: Record<StageName, string> = {
  plan: "The language model writes the scenes",
  verify: "Every step runs on the real structure",
  quiz: "Questions with computed answers",
  voice: "Narration, spoken on this computer",
  draw: "Each scene is animated",
  join: "The clips become one video",
};

/** The current time, ticking once a second while `active`. */
function useNow(active: boolean): number {
  const [now, setNow] = useState(() => Date.now() / 1000);
  useEffect(() => {
    if (!active) return;
    const timer = window.setInterval(() => setNow(Date.now() / 1000), 1000);
    return () => window.clearInterval(timer);
  }, [active]);
  return now;
}

export function PipelineRail({ job }: { job: JobState }) {
  const { scenes } = job;
  const now = useNow(Object.values(job.stages).some((s) => s?.status === "running"));
  return (
    <ol className="rail" aria-label="Pipeline progress">
      {STAGES.map((stage, i) => {
        const s = job.stages[stage];
        const status = s?.status ?? "waiting";
        const rejected = job.rejected.filter((r) => (stage === "plan" ? r.stage === "plan" || r.stage === "revise" : r.stage === stage));
        let detail = s?.detail ?? WAITING[stage];
        let progress: number | null = null;
        if (status === "running" && stage === "voice" && scenes.total) {
          detail = `Scene ${Math.min(scenes.voiced + 1, scenes.total)} of ${scenes.total}`;
          progress = scenes.voiced / scenes.total;
        }
        if (status === "running" && stage === "draw" && scenes.total) {
          const ready = Object.keys(job.clips).length;
          detail = `${ready} of ${scenes.total} scenes ready`;
          progress = ready / scenes.total;
        }
        if (status === "running" && stage === "plan" && job.message) detail = job.message;
        return (
          <li key={stage} className={status}>
            <span className="bubble" aria-hidden="true">
              {status === "done" ? "✓" : status === "failed" ? "!" : status === "skipped" ? "–" : i + 1}
            </span>
            <div>
              <div className="name">
                {NAMES[stage]}
                {status === "running" && <Spinner />}
                {s?.seconds != null && <span className="time">{s.seconds.toFixed(1)} s</span>}
                {status === "running" && s?.started != null && (
                  <span className="time" aria-label="Running for">{Math.max(0, Math.round(now - s.started))} s</span>
                )}
              </div>
              <div className="detail">{detail}</div>
              {progress != null && <div className="bar"><span style={{ width: `${Math.round(progress * 100)}%` }} /></div>}
              {rejected.length > 0 && (
                <ul className="rejections" aria-label="Sent back by the verifier">
                  {rejected.map((r, k) => <li key={k}><b>Attempt {r.attempt} sent back:</b> {r.reason}</li>)}
                </ul>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
