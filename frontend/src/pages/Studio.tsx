import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, LEVELS, type Level, type Quality, QUALITY_LABELS, useHealth, useInvalidate, useLesson, useSettings } from "../api";
import { Helper } from "../components/art";
import { LessonView } from "../components/LessonView";
import { PipelineRail } from "../components/Pipeline";
import { ProgressivePlayer } from "../components/Player";
import { Button, ErrorNotice, Loading, Notice, Segmented } from "../components/ui";
import { useJob } from "../useJob";

const EXAMPLES = [
  "How does a stack work?",
  "Show how a queue handles print jobs",
  "Bubble sort on 5, 1, 4, 2, 8",
  "Binary search for 23 in 2, 5, 8, 12, 16, 23, 38",
  "Insert 8, 3, 10, 1, 6, 14 into a BST, then delete 3",
  "Dijkstra from A: A-B 4, A-C 1, C-B 2, B-D 5",
  "Fewest coins for 6 with coins 1, 3 and 4",
];

export function Composer() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { data: health } = useHealth();
  const { data: settings } = useSettings();
  const [topic, setTopic] = useState(params.get("topic") ?? "");
  const [level, setLevel] = useState<Level>((params.get("level") as Level) || "beginner");
  const [quality, setQuality] = useState<Quality | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const chosenQuality = quality ?? settings?.preferences.default_quality ?? "draft";
  const configured = health?.llm.configured;

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const job = await api.createLesson(topic.trim(), level, chosenQuality);
      navigate(`/studio/job/${job.id}`);
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  }

  return (
    <div className="container page">
      <form className="composer" onSubmit={(e) => { e.preventDefault(); if (topic.trim().length >= 3) submit(); }}>
        <div className="page-head" style={{ alignItems: "center", textAlign: "center", marginBottom: 8 }}>
          <svg width="132" height="90" viewBox="-110 -66 220 150" aria-hidden="true"><Helper r={60} /></svg>
          <h1 className="page-title">What do you want to see?</h1>
          <p>Name a data structure or algorithm, and give your own data if you like.</p>
        </div>
        {health && !configured && (
          <Notice tone="blue">
            <span>To make lessons from your own topics, <Link to="/settings#language-model">add a language-model key</Link>.
              Until then, every lesson in the <Link to="/library">library</Link> plays without one.</span>
          </Notice>
        )}
        <label className="visually-hidden" htmlFor="topic">Topic</label>
        <textarea id="topic" className="textarea topic" value={topic} onChange={(e) => setTopic(e.target.value)} maxLength={500}
          placeholder="e.g. Show quick sort on 5, 1, 4, 2, 8, 3" autoFocus
          onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && topic.trim().length >= 3) submit(); }} />
        <div className="chips" aria-label="Examples">
          {EXAMPLES.map((ex) => <button key={ex} type="button" className="chip" onClick={() => setTopic(ex)}>{ex}</button>)}
        </div>
        <div className="options">
          <div className="field"><span className="label">Level</span>
            <Segmented label="Level" options={LEVELS} value={level} onChange={setLevel} /></div>
          <div className="field"><span className="label">Video quality</span>
            <Segmented<Quality> label="Video quality" options={["draft", "standard", "high"]} value={chosenQuality} onChange={setQuality}
              labels={{ draft: "Draft", standard: "720p", high: "1080p" }} /></div>
        </div>
        <ErrorNotice error={error} />
        <div style={{ display: "flex", justifyContent: "center" }}>
          <Button type="submit" wide disabled={busy || topic.trim().length < 3 || !configured}>{busy ? "Starting…" : "Make my lesson"}</Button>
        </div>
        <p className="small" style={{ textAlign: "center" }}>{QUALITY_LABELS[chosenQuality]}. Higher quality takes longer to draw.
          Or <Link to="/library">start from a saved lesson</Link>.</p>
      </form>
    </div>
  );
}

const KIND_TITLES = { create: "New lesson", render: "Saved lesson", revise: "Revision" } as const;

export function JobPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const invalidate = useInvalidate();
  const job = useJob(jobId);
  const { data: snapshot, error: snapError } = useQuery({ queryKey: ["job", jobId], queryFn: () => api.job(jobId!), enabled: !!jobId });
  const [version, setVersion] = useState<number | undefined>(undefined);
  const result = job.result;
  const { data: lesson } = useLesson(job.status === "done" ? result?.lesson_id : undefined, version ?? result?.version);

  useEffect(() => { if (job.status === "done") invalidate("lessons", "health"); }, [job.status]); // eslint-disable-line react-hooks/exhaustive-deps

  if (snapError) return <div className="container page"><ErrorNotice error={snapError} /><p><Link to="/studio">Start a new lesson</Link></p></div>;
  const params = (snapshot?.params ?? {}) as Record<string, string>;
  const title = params.topic || params.request || (params.plan ? `Saved lesson: ${params.plan.replace(/_/g, " ")}` : "Your lesson");
  const running = job.status === "running" || job.status === "queued" || job.status === "connecting";
  const t = (name: keyof typeof job.stages) => job.stages[name]?.seconds ?? 0;
  // voice and drawing run at the same time, so count the longer of the two
  const totalSeconds = t("plan") + t("quiz") + t("verify") + Math.max(t("voice"), t("draw")) + t("join");

  return (
    <div className="container wide page">
      <div className="studio">
        <aside className="side">
          <span className="eyebrow">{snapshot ? KIND_TITLES[snapshot.kind] : "Lesson"}</span>
          <p className="job-topic">{title}</p>
          <PipelineRail job={job} />
          {running && <Button variant="danger" small onClick={() => api.cancelJob(jobId!)}>Cancel</Button>}
          {job.status === "done" && <Notice tone="green"><span><b>Done</b>{totalSeconds ? ` in about ${Math.round(totalSeconds)} s` : ""}. Every step was checked.</span></Notice>}
          {job.status === "failed" && (
            <>
              <Notice tone="red"><span><b>No video was made.</b> {job.error}</span></Notice>
              <p className="small">A wrong video is worse than no video, so the pipeline stops when a plan cannot be verified.
                Try rewording the topic or giving the data yourself.</p>
              <div className="actions-row">
                {snapshot?.kind === "create" && <Button small onClick={() => navigate(`/studio?topic=${encodeURIComponent(params.topic ?? "")}&level=${params.level ?? "beginner"}`)}>Edit topic</Button>}
                {snapshot?.kind === "revise" && <Button small variant="secondary" onClick={() => navigate(`/lessons/${params.lesson_id}`)}>Back to the lesson</Button>}
              </div>
            </>
          )}
          {job.status === "cancelled" && <Notice><span>Cancelled. <Link to="/studio">Start again</Link></span></Notice>}
        </aside>
        <section aria-live="polite">
          {job.status === "done" && lesson ? (
            <LessonView lesson={lesson} onVersion={setVersion} />
          ) : job.status === "done" ? (
            <Loading what="Opening your lesson" />
          ) : (
            <ProgressivePlayer clips={job.clips} total={job.scenes.total} finished={job.stages.join?.status === "running"} />
          )}
        </section>
      </div>
    </div>
  );
}
