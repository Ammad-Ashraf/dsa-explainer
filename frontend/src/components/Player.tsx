import { useEffect, useMemo, useRef, useState } from "react";
import { type Chapter, type Cue, cuesToVtt } from "../api";
import type { Clip } from "../useJob";
import { Spinner } from "./ui";

const label = (name: string) => name.replace(/^\w/, (c) => c.toUpperCase());

/** A captions track for one clip, from the cues its clip event carried. */
function useCuesUrl(cues: Cue[] | undefined): string | undefined {
  const url = useMemo(() => (cues?.length ? URL.createObjectURL(new Blob([cuesToVtt(cues)], { type: "text/vtt" })) : undefined), [cues]);
  useEffect(() => () => { if (url) URL.revokeObjectURL(url); }, [url]);
  return url;
}

/** Plays finished clips in order while the rest are still being drawn. */
export function ProgressivePlayer({ clips, total, finished }: { clips: Record<number, Clip>; total: number; finished: boolean }) {
  const video = useRef<HTMLVideoElement>(null);
  const [index, setIndex] = useState(0);
  const [started, setStarted] = useState(false);
  const current = clips[index];
  const waiting = started && !current && index < total;
  const track = useCuesUrl(current?.cues);

  useEffect(() => {
    if (started && current && video.current) {
      video.current.play().catch(() => setStarted(false));
    }
  }, [current?.key, started]); // eslint-disable-line react-hooks/exhaustive-deps

  const ready = Object.keys(clips).length;
  return (
    <div className="stage">
      <div className="screen">
        {current && (
          <video ref={video} key={current.key} src={`/api/clips/${current.key}`} controls={started} playsInline
            onEnded={() => setIndex((i) => i + 1)}>
            {track && <track kind="captions" srcLang="en" label="English" src={track} />}
          </video>
        )}
        {!started && (
          <div className={`overlay${current ? "" : " solid"}`}>
            {current ? (
              <>
                <strong>The first scenes are ready</strong>
                <span>Start watching while the rest are drawn.</span>
                <button type="button" className="btn btn-primary" onClick={() => setStarted(true)}>Play {label(current.name)}</button>
              </>
            ) : (
              <>
                <Spinner />
                <strong>{finished ? "Almost there" : "Your lesson is being made"}</strong>
                <span>Scenes appear here as soon as they are drawn.</span>
              </>
            )}
          </div>
        )}
        {waiting && (
          <div className="overlay">
            <Spinner />
            <strong>Drawing the next scene</strong>
            <span>{ready} of {total} ready</span>
          </div>
        )}
        {started && current && <span className="badge">Preview · scene {index + 1} of {total || "?"}</span>}
      </div>
      <div className="chapters" aria-label="Scenes" style={{ "--cols": Math.ceil(total / 2) } as React.CSSProperties}>
        {Array.from({ length: total }, (_, i) => clips[i]).map((clip, i) => (
          <button key={i} type="button" className={`chapter${i === index && started ? " current" : ""}${clip ? " ready" : " pending"}`}
            disabled={!clip} onClick={() => { setIndex(i); setStarted(true); }}>
            <span className="n">{clip ? label(clip.name) : `Scene ${i + 1}`}</span>
            <span className="op">{clip ? `${clip.seconds.toFixed(0)} s` : "drawing…"}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

/** The finished video, with a chapter strip that follows playback and seeks on click. */
export function LessonPlayer({ src, captions, chapters, ops }: {
  src: string; captions?: string; chapters: Chapter[]; ops: Record<string, string | null>;
}) {
  const video = useRef<HTMLVideoElement>(null);
  const [time, setTime] = useState(0);
  const current = chapters.findIndex((c, i) => time >= c.start && (i === chapters.length - 1 || time < chapters[i + 1].start));
  return (
    <div className="stage">
      <div className="screen">
        <video ref={video} key={src} src={src} controls playsInline preload="metadata"
          onTimeUpdate={(e) => setTime(e.currentTarget.currentTime)}>
          {/* off until the learner turns it on (CC): every scene already shows its own short caption */}
          {captions && <track kind="captions" srcLang="en" label="English" src={captions} />}
        </video>
      </div>
      {chapters.length > 0 && (
        <div className="chapters" aria-label="Chapters" style={{ "--cols": Math.ceil(chapters.length / 2) } as React.CSSProperties}>
          {chapters.map((c, i) => (
            <button key={c.name} type="button" className={`chapter${i === current ? " current" : ""}`}
              onClick={() => { if (video.current) { video.current.currentTime = c.start + 0.01; video.current.play().catch(() => {}); } }}>
              <span className="n">{label(c.name)}</span>
              <span className="op">{ops[c.name] ?? `${Math.round(c.seconds)} s`}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
