import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { algorithmById, api, formatSeconds, type LessonDetail, QUALITY_LABELS, useCatalog } from "../api";
import { LessonPlayer } from "./Player";
import { Button, ErrorNotice, LevelTag, Notice, Tabs, Tag } from "./ui";

type Tab = "quiz" | "verified" | "change" | "transcript" | "plan";

export function Quiz({ questions, structure }: { questions: LessonDetail["quiz"]; structure: string }) {
  const [picked, setPicked] = useState<Record<number, number>>({});
  if (!questions.length) return <p>This lesson has no quiz.</p>;
  const score = Object.entries(picked).filter(([q, o]) => questions[+q].answer === o).length;
  const done = Object.keys(picked).length === questions.length;
  return (
    <div>
      {questions.map((q, i) => {
        const choice = picked[i];
        return (
          <div key={i} className="quiz-q">
            <span className="eyebrow">Question {i + 1} of {questions.length}</span>
            <h3>{q.question}</h3>
            <div className="quiz-options">
              {q.options.map((o, k) => {
                const state = choice == null ? "" : k === q.answer ? " right" : k === choice ? " wrong" : "";
                return (
                  <button key={k} type="button" className={`quiz-option${state}`} disabled={choice != null}
                    onClick={() => setPicked({ ...picked, [i]: k })}>
                    <span className="letter">{"ABCD"[k]}</span>{o}
                  </button>
                );
              })}
            </div>
            {choice != null && (
              <Notice tone={choice === q.answer ? "green" : "blue"}>
                <span><b>{choice === q.answer ? "Right!" : `The answer is ${"ABCD"[q.answer]}.`}</b> {q.explanation}{" "}
                  <span className="small">(Checked by running the operations on a real {structure}.)</span></span>
              </Notice>
            )}
          </div>
        );
      })}
      {done && <p className="lead ink" style={{ marginTop: 20 }}>You got {score} of {questions.length}{score === questions.length ? ". Perfect!" : "."}</p>}
    </div>
  );
}

function Verified({ lesson }: { lesson: LessonDetail }) {
  const v = lesson.version_info;
  const t = v.timings ?? {};
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <Notice tone={lesson.verified.ok ? "green" : "red"}>
        <span>
          <b>{lesson.verified.ok ? `${lesson.verified.checks} checks passed.` : "This version failed verification."}</b>{" "}
          Every step was run on a real data structure; the planned states, the facts in the narration and the quiz
          answers all match it.
        </span>
      </Notice>
      <div className="stats">
        <div className="stat"><b>{formatSeconds(v.seconds)}</b><span>of video</span></div>
        <div className="stat"><b>{v.clips ?? "–"}</b><span>scenes</span></div>
        <div className="stat"><b>{v.rendered?.length ?? "–"}</b><span>drawn for this version</span></div>
        <div className="stat"><b>{v.reused ?? "–"}</b><span>reused from the cache</span></div>
        {t.plan_seconds != null && <div className="stat"><b>{formatSeconds(t.plan_seconds)}</b><span>planning</span></div>}
        {t.voice_seconds != null && <div className="stat"><b>{formatSeconds(t.voice_seconds)}</b><span>voice</span></div>}
        {t.build_seconds != null && <div className="stat"><b>{formatSeconds(t.build_seconds)}</b><span>voice and drawing</span></div>}
      </div>
      {v.rejected && v.rejected.length > 0 && (
        <div>
          <h3 className="section-title" style={{ fontSize: 20, marginBottom: 10 }}>Sent back before this plan was accepted</h3>
          <ul className="rejections">{v.rejected.map((r, i) => <li key={i}>{r}</li>)}</ul>
        </div>
      )}
      {v.request && <p><b className="ink">Change requested:</b> “{v.request}” (changed {v.changed?.join(", ")})</p>}
    </div>
  );
}

function ChangeIt({ lesson }: { lesson: LessonDetail }) {
  const navigate = useNavigate();
  const [text, setText] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const steps = lesson.scenes.filter((s) => s.kind === "step").length;
  const ideas = ["Slow down step 2", "Explain step 1 for a beginner", `Speed up step ${steps}`, "Explain the summary in more detail",
    "Explain it for an advanced learner"];
  async function submit(request: string) {
    setBusy(true);
    setError(null);
    try {
      const job = await api.revise(lesson.id, request, lesson.version);
      navigate(`/studio/job/${job.id}`);
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  }
  return (
    <form style={{ display: "flex", flexDirection: "column", gap: 16 }} onSubmit={(e) => { e.preventDefault(); if (text.trim()) submit(text.trim()); }}>
      <div className="field">
        <label htmlFor="change">What should change?</label>
        <input id="change" className="input" value={text} onChange={(e) => setText(e.target.value)}
          placeholder="e.g. slow down step 3, or explain step 2 more simply" maxLength={500} />
        <span className="hint">Speed changes work without a language model. Rewrites keep every fact true: the new
          narration is checked again, and only the scenes you name are redrawn.</span>
      </div>
      <div className="chips">
        {ideas.map((idea) => <button key={idea} type="button" className="chip" onClick={() => setText(idea)}>{idea}</button>)}
      </div>
      <ErrorNotice error={error} />
      <div><Button type="submit" disabled={busy || !text.trim()}>{busy ? "Starting…" : "Make version " + (Math.max(...lesson.versions.map((v) => v.version)) + 1)}</Button></div>
    </form>
  );
}

function Transcript({ lesson }: { lesson: LessonDetail }) {
  return (
    <div className="transcript">
      {lesson.scenes.map((s) => (
        <div key={s.label} className="line">
          <span className="who">{s.label}{s.op && <><br /><span className="mono" style={{ textTransform: "none" }}>{s.op}</span></>}</span>
          <p className="ink">{s.narration}</p>
        </div>
      ))}
    </div>
  );
}

function Plan({ lesson }: { lesson: LessonDetail }) {
  const json = useMemo(() => JSON.stringify(lesson.plan, null, 2), [lesson.plan]);
  const href = useMemo(() => URL.createObjectURL(new Blob([json], { type: "application/json" })), [json]);
  useEffect(() => () => URL.revokeObjectURL(href), [href]);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <p>The verified lesson plan: what the language model wrote, after the verifier accepted it. Claimed states are
        checked against the real structure.</p>
      <div><a className="btn btn-secondary btn-small" href={href} download={`${lesson.id}-v${lesson.version}.json`}>Download plan</a></div>
      <pre className="json">{json}</pre>
    </div>
  );
}

export function LessonView({ lesson, onVersion }: { lesson: LessonDetail; onVersion: (v: number) => void }) {
  const [tab, setTab] = useState<Tab>("quiz");
  const { data: catalog } = useCatalog();
  const algo = algorithmById(catalog, lesson.structure);
  const ops = Object.fromEntries(lesson.scenes.map((s) => [s.label, s.op]));
  const info = lesson.version_info;
  return (
    <div className="stage">
      <div className="page-head" style={{ marginBottom: 0 }}>
        <div className="row">
          <h1 className="page-title">{lesson.title}</h1>
          <a className="btn btn-secondary btn-small" href={lesson.video_url} download={`${lesson.id}-v${lesson.version}.mp4`}>Download video</a>
        </div>
        <div className="actions-row">
          <LevelTag level={lesson.level} />
          {algo && <Link to={`/library/${algo.id}`} className="tag">{algo.title}</Link>}
          {info.quality && <Tag>{QUALITY_LABELS[info.quality]}</Tag>}
          <Tag>{formatSeconds(info.seconds)}</Tag>
        </div>
      </div>
      <LessonPlayer src={lesson.video_url} chapters={info.chapters ?? []} ops={ops} />
      {lesson.versions.length > 1 && (
        <div className="versions" aria-label="Versions">
          <span className="eyebrow">Versions</span>
          {lesson.versions.map((v) => (
            <button key={v.version} type="button" className="chip" aria-pressed={v.version === lesson.version} onClick={() => onVersion(v.version)}
              title={v.request ?? "First version"}>
              v{v.version}{v.request ? `: ${v.request}` : ""}
            </button>
          ))}
        </div>
      )}
      <Tabs<Tab> value={tab} onChange={setTab} tabs={[
        { id: "quiz", label: `Quiz (${lesson.quiz.length})` }, { id: "verified", label: "Verified" },
        { id: "change", label: "Change it" }, { id: "transcript", label: "Transcript" }, { id: "plan", label: "Plan" },
      ]} />
      <div className="tab-panel" role="tabpanel">
        {tab === "quiz" && <Quiz questions={lesson.quiz} structure={(algo?.title ?? lesson.structure).toLowerCase()} />}
        {tab === "verified" && <Verified lesson={lesson} />}
        {tab === "change" && <ChangeIt lesson={lesson} />}
        {tab === "transcript" && <Transcript lesson={lesson} />}
        {tab === "plan" && <Plan lesson={lesson} />}
      </div>
    </div>
  );
}
