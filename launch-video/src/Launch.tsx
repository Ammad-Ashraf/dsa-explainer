import React from "react";
import { AbsoluteFill, Audio, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Backdrop, BrowserFrame, C, type Cam, camera, Card, FONT, Footage, fontFaces, K, Logo, PAGE, Pill, type Seg, segFrames, smooth, WIN, WIN_H, Words } from "./kit";
import { CLOSING, INTRO, SHOTS, type Shot } from "./shots";

const OVERLAP = 18; // frames two shots cross-fade inside the window
const REST = { x: 960, y: 612, scale: 0.84 };
const ZOOM_CENTER = { x: 960, y: 548 };

/** Capture frame -> frame inside the shot, through its segments (each may play faster). */
export function local(shot: Shot, cf: number) {
  let at = 0;
  for (const s of shot.segs) {
    if (cf < s.from) return at;
    if (cf < s.to) return at + (cf - s.from) / (s.rate ?? 1);
    at += segFrames(s);
  }
  return at;
}
export const shotFrames = (shot: Shot) => shot.segs.reduce((n, s) => n + segFrames(s), 0);

function placeWindow(cam: { s: number; x: number; y: number }) {
  const S = REST.scale * cam.s;
  const q = { x: cam.x * K - WIN.w / 2, y: WIN.bar + cam.y * K - WIN_H / 2 };
  const k = Math.min(1, Math.max(0, (cam.s - 1) / 0.35));
  const restQ = { x: REST.x + REST.scale * q.x, y: REST.y + REST.scale * q.y };
  const M = { x: restQ.x + (ZOOM_CENTER.x - restQ.x) * k, y: restQ.y + (ZOOM_CENTER.y - restQ.y) * k };
  const A = { x: M.x - S * q.x, y: M.y - S * q.y };
  return { S, left: A.x - S * WIN.w / 2, top: A.y - S * WIN_H / 2 };
}

function WindowSection({ shots, total }: { shots: Shot[]; total: number }) {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  // where each shot starts
  const starts: number[] = [];
  let at = 0;
  for (const s of shots) { starts.push(at); at += shotFrames(s) - OVERLAP; }
  let idx = 0;
  for (let i = 0; i < shots.length; i++) if (f >= starts[i]) idx = i;
  const shot = shots[idx];
  const lf = f - starts[idx];
  const keys: Cam[] = (shot.cam ?? []).map((c) => ({ ...c, f: local(shot, c.f) }));
  const cam = camera(keys.length ? keys : [{ f: 0, s: 1 }], lf);
  const place = placeWindow(cam);

  const enter = spring({ frame: f, fps, config: { damping: 22, stiffness: 70, mass: 1.1 } });
  const leave = interpolate(f, [total - 26, total], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: smooth });
  const z = Math.min(1, Math.max(0, (cam.s - 1.02) / 0.12)); // 0 at rest, 1 when the camera is zoomed in

  // caption: the latest one whose time has come, across all shots
  const caps = shots.flatMap((s, i) => s.captions.map((c) => ({ ...c, f: starts[i] + local(s, c.at) + (i ? OVERLAP / 2 : 0) })));
  const capIdx = caps.reduce((best, c, i) => (f >= c.f ? i : best), -1);
  const cap = caps[capIdx];
  const next = caps[capIdx + 1];

  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 0, top: 0, transformOrigin: "0 0", perspective: 2400,
        transform: `translate(${place.left}px, ${place.top + (1 - enter) * 260}px) scale(${place.S * (1 - leave * 0.06)})`,
        opacity: Math.min(1, enter * 1.4) * (1 - leave), filter: leave ? `blur(${leave * 10}px)` : undefined }}>
        <div style={{ transform: `rotateX(${(1 - enter) * 22}deg)`, transformOrigin: "50% 100%" }}>
          <BrowserFrame>
            {shots.map((s, i) => {
              const d = shotFrames(s);
              if (f < starts[i] - 2 || f > starts[i] + d + 2) return null;
              const o = i === 0 ? 1 : interpolate(f - starts[i], [0, OVERLAP], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
              return (
                <Sequence key={i} from={starts[i]} durationInFrames={d} layout="none">
                  <div style={{ position: "absolute", inset: 0, opacity: o }}><Footage src={s.src} segs={s.segs} /></div>
                </Sequence>
              );
            })}
          </BrowserFrame>
        </div>
      </div>
      {cap && (
        <div style={{ position: "absolute", left: 0, right: 0, top: 70 + z * 850, display: "flex", justifyContent: "center", opacity: 1 - leave }}>
          <div style={{ padding: `${14 * z}px ${36 * z}px`, borderRadius: 999, background: `rgba(255,255,255,${0.94 * z})`,
            boxShadow: `0 18px 40px -12px rgba(0,0,0,${0.22 * z})`, transform: `scale(${1 - 0.24 * z})`, transformOrigin: "50% 50%" }}>
            <Sequence key={capIdx} from={cap.f} layout="none">
              <Words text={cap.text} size={56} highlight={cap.hl} stagger={3} exitAt={next ? next.f - cap.f - 16 : undefined} />
            </Sequence>
          </div>
        </div>
      )}
      {shots.map((s, i) => (s.pills ?? []).map((p, k) => (
        <Pill key={`${i}-${k}`} appear={starts[i] + local(s, p.at)} leave={starts[i] + local(s, p.until)}
          style={{ right: 70, bottom: 44 }}>{p.text}</Pill>
      )))}
    </AbsoluteFill>
  );
}

function Stats({ dur }: { dur: number }) {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const items = [
    { n: 22, suffix: "", label: "algorithms with ready-made lessons" },
    { n: 97, suffix: "%", label: "of 601 planted mistakes caught" },
    { n: 303, suffix: "", label: "automated tests" },
  ];
  const leave = interpolate(f, [dur - 18, dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: smooth });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: 1 - leave, filter: `blur(${leave * 8}px)` }}>
      <div style={{ display: "flex", gap: 120 }}>
        {items.map((it, i) => {
          const s = spring({ frame: f - 6 - i * 10, fps, config: { damping: 20, stiffness: 90 } });
          const count = Math.round(interpolate(f - 6 - i * 10, [0, 55], [0, it.n], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: smooth }));
          return (
            <div key={i} style={{ textAlign: "center", opacity: s, transform: `translateY(${(1 - s) * 40}px)`, width: 380 }}>
              <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 150, color: i === 1 ? C.green : C.ink, lineHeight: 1, fontVariantNumeric: "tabular-nums" }}>
                {count}{it.suffix}</div>
              <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: 30, color: C.body, marginTop: 18 }}>{it.label}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
}

function Outro() {
  const f = useCurrentFrame();
  const fade = interpolate(f, [20, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 34 }}>
      <Logo size={1.1} />
      <div style={{ opacity: fade, transform: `translateY(${(1 - fade) * 14}px)`, textAlign: "center" }}>
        <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 40, color: C.ink }}>Open source. Runs on your computer.</div>
        <div style={{ fontFamily: FONT, fontWeight: 800, fontSize: 30, color: C.blue, marginTop: 22 }}>github.com/Ammad-Ashraf/dsa-explainer</div>
        <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: 26, color: C.body, marginTop: 40 }}>Made by Ahmed Javaid and Ammad Ashraf</div>
      </div>
    </AbsoluteFill>
  );
}

function LogoCard({ dur }: { dur: number }) {
  const f = useCurrentFrame();
  const leave = interpolate(f, [dur - 18, dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: smooth });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 36, opacity: 1 - leave, transform: `scale(${1 - leave * 0.05})` }}>
      <Logo delay={4} />
      <Words text="Verified, narrated algorithm lessons, made on your own computer." size={38} weight={700} color={C.body} delay={30} stagger={2} />
    </AbsoluteFill>
  );
}

/** The whole timeline, worked out once: what plays when. */
export function timeline() {
  const parts: { kind: string; from: number; dur: number; text?: string; hl?: string[]; size?: number }[] = [];
  let at = 0;
  for (const c of INTRO) { parts.push({ kind: "card", from: at, dur: c.dur, text: c.text, hl: c.hl, size: c.size }); at += c.dur; }
  parts.push({ kind: "logo", from: at, dur: 190 }); at += 190;
  const win = SHOTS.reduce((n, s) => n + shotFrames(s) - OVERLAP, OVERLAP);
  const winFrom = at - 10;
  parts.push({ kind: "window", from: winFrom, dur: win }); at = winFrom + win;
  for (const c of CLOSING) { parts.push({ kind: c.kind, from: at, dur: c.dur, text: c.text, hl: c.hl, size: c.size }); at += c.dur; }
  // lesson narration: where it plays in the final video
  const starts: number[] = [];
  let s0 = 0;
  for (const s of SHOTS) { starts.push(s0); s0 += shotFrames(s) - OVERLAP; }
  const voice = SHOTS.flatMap((s, i) => (s.audio ?? []).map((a) => ({ from: winFrom + starts[i] + local(s, a.frame), frames: a.frames, start: a.start })));
  return { parts, total: at, voice };
}

export const Launch: React.FC = () => {
  const { parts, total, voice } = timeline();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ fontFamily: FONT }}>
      <style>{fontFaces}</style>
      <Backdrop />
      {parts.map((p, i) => (
        <Sequence key={i} from={p.from} durationInFrames={p.dur}>
          {p.kind === "card" && <Card text={p.text!} highlight={p.hl} dur={p.dur} size={p.size} />}
          {p.kind === "logo" && <LogoCard dur={p.dur} />}
          {p.kind === "window" && <WindowSection shots={SHOTS} total={p.dur} />}
          {p.kind === "stats" && <Stats dur={p.dur} />}
          {p.kind === "outro" && <Outro />}
        </Sequence>
      ))}
      <Audio src={staticFile("music.wav")} volume={(f) => {
        const duck = Math.max(0, ...voice.map((v) => interpolate(f, [v.from - 30, v.from, v.from + v.frames, v.from + v.frames + 40], [0, 1, 1, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" })));
        const fadeOut = interpolate(f, [total - 150, total], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return (0.55 - 0.43 * duck) * fadeOut;
      }} />
      {voice.map((v, i) => (
        <Sequence key={i} from={Math.round(v.from)} durationInFrames={v.frames}>
          <Audio src={staticFile("bst-lesson.mp4")} startFrom={Math.round(v.start * fps)} volume={(f) =>
            interpolate(f, [0, 8, v.frames - 12, v.frames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

export const PAGE_SIZE = PAGE;
