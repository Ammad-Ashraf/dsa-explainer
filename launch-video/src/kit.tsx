import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, OffthreadVideo, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

export const C = {
  green: "#58cc02", greenShade: "#46a302", greenWash: "#d7ffb8", blue: "#1cb0f6", sky: "#ddf4ff", skyInk: "#042c60",
  ink: "#3c3c3c", body: "#6f6f6f", muted: "#afafaf", rule: "#e5e5e5", bg: "#fbfbf8",
};
export const FONT = "Nunito, system-ui, sans-serif";

export const fontFaces = `
@font-face { font-family: Nunito; font-weight: 700; src: url(${staticFile("nunito-latin-700-normal.woff2")}) format("woff2"); }
@font-face { font-family: Nunito; font-weight: 800; src: url(${staticFile("nunito-latin-800-normal.woff2")}) format("woff2"); }
@font-face { font-family: Nunito; font-weight: 900; src: url(${staticFile("nunito-latin-900-normal.woff2")}) format("woff2"); }
`;

export const smooth = Easing.bezier(0.65, 0, 0.35, 1);
export const out = Easing.bezier(0.16, 1, 0.3, 1);

/** Soft off-white backdrop with two slow, blurred colour fields. */
export function Backdrop() {
  const f = useCurrentFrame();
  const a = f / 240;
  return (
    <AbsoluteFill style={{ background: C.bg, overflow: "hidden" }}>
      <div style={{ position: "absolute", width: 1100, height: 1100, borderRadius: "50%", filter: "blur(140px)", opacity: 0.32,
        background: C.greenWash, left: -260 + Math.sin(a) * 80, top: -420 + Math.cos(a * 0.8) * 60 }} />
      <div style={{ position: "absolute", width: 1000, height: 1000, borderRadius: "50%", filter: "blur(150px)", opacity: 0.4,
        background: C.sky, right: -300 + Math.cos(a * 0.9) * 90, bottom: -460 + Math.sin(a * 0.7) * 70 }} />
      {/* faint dot grid */}
      <AbsoluteFill style={{ opacity: 0.35, backgroundImage: "radial-gradient(#d9ddd4 1.2px, transparent 1.2px)", backgroundSize: "28px 28px",
        maskImage: "radial-gradient(ellipse at center, black 30%, transparent 75%)" }} />
    </AbsoluteFill>
  );
}

/** Words that rise into place one after another, then (optionally) leave together. */
export function Words({ text, delay = 0, stagger = 4, size = 84, weight = 900, color = C.ink, exitAt, highlight = [], align = "center", lineHeight = 1.12 }: {
  text: string; delay?: number; stagger?: number; size?: number; weight?: number; color?: string; exitAt?: number;
  highlight?: string[]; align?: "center" | "left"; lineHeight?: number;
}) {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const lines = text.split("\n");
  let k = 0;
  const exit = exitAt == null ? 0 : interpolate(f, [exitAt, exitAt + 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: smooth });
  return (
    <div style={{ fontFamily: FONT, fontWeight: weight, fontSize: size, color, lineHeight, letterSpacing: -0.5, textAlign: align,
      opacity: 1 - exit, transform: `translateY(${-24 * exit}px)`, filter: `blur(${exit * 8}px)` }}>
      {lines.map((line, li) => (
        <div key={li} style={{ display: "flex", flexWrap: "wrap", justifyContent: align === "center" ? "center" : "flex-start", columnGap: size * 0.26 }}>
          {line.split(" ").map((w, wi) => {
            const s = spring({ frame: f - delay - k++ * stagger, fps, config: { damping: 18, stiffness: 120, mass: 0.7 } });
            const hl = highlight.includes(w.replace(/[.,!?]/g, ""));
            return (
              <span key={wi} style={{ display: "inline-block", opacity: s, transform: `translateY(${(1 - s) * size * 0.55}px)`,
                filter: `blur(${(1 - s) * 10}px)`, color: hl ? C.green : undefined }}>{w}</span>
            );
          })}
        </div>
      ))}
    </div>
  );
}

/** A full-frame title card. */
export function Card({ text, sub, highlight, dur, size = 92 }: { text: string; sub?: string; highlight?: string[]; dur: number; size?: number }) {
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: 160 }}>
      <Words text={text} size={size} highlight={highlight} exitAt={dur - 18} />
      {sub && <div style={{ marginTop: 30 }}><Words text={sub} size={36} weight={700} color={C.body} delay={14} stagger={2} exitAt={dur - 18} /></div>}
    </AbsoluteFill>
  );
}

// ---------------------------------------------------------------------------------------------------------------
// The browser window and its camera

export const WIN = { w: 1600, bar: 46 };
export const PAGE = { w: 1440, h: 810 };
export const K = WIN.w / PAGE.w; // page css px -> window px
export const WIN_H = WIN.bar + PAGE.h * K;

export type Cam = { f: number; s: number; x?: number; y?: number };

/**
 * Camera keyframes: zoom `s` about the page point (x, y) in page CSS pixels. Without x/y the camera sits at rest.
 * Returns the transform for the window, relative to its resting place.
 */
export function camera(keys: Cam[], f: number) {
  const pts = keys.map((k) => ({ f: k.f, s: k.s, x: k.x ?? PAGE.w / 2, y: k.y ?? PAGE.h / 2 + WIN.bar / K / 2 }));
  if (!pts.length) return { s: 1, x: PAGE.w / 2, y: PAGE.h / 2 };
  let i = pts.findIndex((p) => p.f > f);
  if (i === -1) return pts[pts.length - 1];
  if (i === 0) return pts[0];
  const a = pts[i - 1], b = pts[i];
  const t = smooth((f - a.f) / (b.f - a.f));
  return { s: a.s + (b.s - a.s) * t, x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t };
}

export function BrowserFrame({ children, url = "localhost:8000" }: { children: React.ReactNode; url?: string }) {
  return (
    <div style={{ width: WIN.w, height: WIN_H, borderRadius: 18, overflow: "hidden", background: "#fff",
      boxShadow: "0 50px 100px -20px rgba(30,50,20,.28), 0 30px 60px -30px rgba(0,0,0,.3), 0 0 0 1px rgba(0,0,0,.06)" }}>
      <div style={{ height: WIN.bar, background: "#f3f3f1", borderBottom: "1px solid #e6e6e3", display: "flex", alignItems: "center", padding: "0 18px", gap: 9 }}>
        {["#ff5f57", "#febc2e", "#28c840"].map((c) => <span key={c} style={{ width: 13, height: 13, borderRadius: 7, background: c }} />)}
        <div style={{ margin: "0 auto", transform: "translateX(-30px)", width: 420, height: 28, borderRadius: 8, background: "#fff",
          border: "1px solid #e6e6e3", display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
          fontFamily: FONT, fontWeight: 700, fontSize: 15, color: "#8a8a8a" }}>
          <svg width="11" height="13" viewBox="0 0 11 13"><rect x="1" y="5.5" width="9" height="7" rx="1.5" fill="#9a9a9a" /><path d="M3 5.5V4a2.5 2.5 0 0 1 5 0v1.5" stroke="#9a9a9a" strokeWidth="1.6" fill="none" /></svg>
          {url}
        </div>
      </div>
      <div style={{ position: "relative", width: WIN.w, height: PAGE.h * K, overflow: "hidden" }}>{children}</div>
    </div>
  );
}

/** One continuous piece of a capture: frames [from, to) played at `rate`. */
export type Seg = { from: number; to: number; rate?: number };
export const segFrames = (s: Seg) => Math.round((s.to - s.from) / (s.rate ?? 1));

export function Footage({ src, segs }: { src: string; segs: Seg[] }) {
  let at = 0;
  return (
    <>
      {segs.map((s, i) => {
        const d = segFrames(s);
        const el = (
          <Sequence key={i} from={at} durationInFrames={d} layout="none">
            <OffthreadVideo src={staticFile(src)} startFrom={s.from} endAt={s.to} playbackRate={s.rate ?? 1} muted
              style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }} />
          </Sequence>
        );
        at += d;
        return el;
      })}
    </>
  );
}

export function Logo({ size = 1, delay = 0 }: { size?: number; delay?: number }) {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: f - delay, fps, config: { damping: 11, stiffness: 140 } });
  const slide = spring({ frame: f - delay - 8, fps, config: { damping: 20, stiffness: 110 } });
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 26 * size }}>
      <Img src={staticFile("helper.png")} style={{ width: 120 * size, transform: `scale(${pop}) rotate(${(1 - pop) * -25}deg)` }} />
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 104 * size, color: C.green, letterSpacing: -1,
        opacity: slide, transform: `translateX(${(1 - slide) * -40}px)`, clipPath: `inset(0 ${(1 - slide) * 100}% 0 0)` }}>dsa explainer</div>
    </div>
  );
}

/** A small rounded label, used for "timelapse" and similar notes on the footage. */
export function Pill({ children, appear, leave, style }: { children: React.ReactNode; appear: number; leave: number; style?: React.CSSProperties }) {
  const f = useCurrentFrame();
  const o = interpolate(f, [appear, appear + 12, leave - 12, leave], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", opacity: o, transform: `translateY(${(1 - o) * 12}px)`, fontFamily: FONT, fontWeight: 800, fontSize: 24,
      color: "#fff", background: "rgba(40,44,38,.82)", backdropFilter: "blur(8px)", borderRadius: 999, padding: "10px 22px",
      display: "flex", alignItems: "center", gap: 10, ...style }}>{children}</div>
  );
}
