// Building blocks for the illustrations, following docs/design/design-system.md: flat rounded shapes, a darker
// offset "side face" instead of blurred shadows, saturated colours on white.
import type { ReactNode } from "react";

export const C = {
  green: "#58cc02", greenSide: "#46a302", greenLight: "#89e219", greenWash: "#d7ffb8",
  blue: "#1cb0f6", blueSide: "#1899d6", blueWash: "#ddf4ff",
  yellow: "#ffc800", yellowSide: "#e5a800",
  orange: "#ff9600", orangeSide: "#e08400",
  pink: "#ff86d0", pinkSide: "#e66bb6",
  purple: "#ce82ff", purpleSide: "#a568cc",
  red: "#ff4b4b",
  ink: "#4b4b4b", inkSide: "#333333", muted: "#afafaf", rule: "#e5e5e5", white: "#ffffff",
};

const FONT = "Nunito, 'Nunito Sans', sans-serif";

/** Floats its children gently (see .float in styles.css). `delay` staggers neighbours. */
export function Float({ children, delay = 0, slow }: { children: ReactNode; delay?: number; slow?: boolean }) {
  return <g className={slow ? "float float-slow" : "float"} style={{ animationDelay: `${delay}s` }}>{children}</g>;
}

/** Places and tilts a group. A separate group from Float, so CSS motion never overrides the placement. */
export function At({ x, y, rotate = 0, scale = 1, children }: { x: number; y: number; rotate?: number; scale?: number; children: ReactNode }) {
  return <g transform={`translate(${x} ${y}) rotate(${rotate}) scale(${scale})`}>{children}</g>;
}

export function Label({ x, y, children, size = 14, fill = C.ink, anchor = "middle", weight = 800 }:
  { x: number; y: number; children: ReactNode; size?: number; fill?: string; anchor?: "start" | "middle" | "end"; weight?: number }) {
  return <text x={x} y={y} textAnchor={anchor} fontSize={size} fontWeight={weight} fill={fill} fontFamily={FONT}>{children}</text>;
}

/** A rounded rectangle with a darker lower edge. */
export function Block({ x, y, w, h, r = 10, face, side, dy = 5, stroke }:
  { x: number; y: number; w: number; h: number; r?: number; face: string; side: string; dy?: number; stroke?: string }) {
  return (
    <>
      <rect x={x} y={y + dy} width={w} height={h} rx={r} fill={side} />
      <rect x={x} y={y} width={w} height={h} rx={r} fill={face} stroke={stroke} strokeWidth={stroke ? 3 : 0} />
    </>
  );
}

/** A circle with a darker lower edge. */
export function Dot({ cx, cy, r, face, side, dy = 4 }: { cx: number; cy: number; r: number; face: string; side: string; dy?: number }) {
  return (
    <>
      <circle cx={cx} cy={cy + dy} r={r} fill={side} />
      <circle cx={cx} cy={cy} r={r} fill={face} />
    </>
  );
}

export function starPath(cx: number, cy: number, outer: number, inner: number) {
  const pts = Array.from({ length: 10 }, (_, i) => {
    const r = i % 2 ? inner : outer;
    const a = (Math.PI / 5) * i - Math.PI / 2;
    return `${(cx + r * Math.cos(a)).toFixed(1)},${(cy + r * Math.sin(a)).toFixed(1)}`;
  });
  return `M ${pts.join(" L ")} Z`;
}

/** A tilted phone or tablet; the screen is drawn by `children`, centred on (0, 0). */
export function Device({ w = 150, h = 210, children }: { w?: number; h?: number; children?: ReactNode }) {
  return (
    <g>
      <rect x={-w / 2} y={-h / 2 + 9} width={w} height={h} rx={24} fill={C.inkSide} />
      <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={24} fill={C.ink} />
      <rect x={-w / 2 + 10} y={-h / 2 + 12} width={w - 20} height={h - 34} rx={15} fill={C.blueWash} />
      <rect x={-14} y={h / 2 - 15} width={28} height={6} rx={3} fill="#666" />
      <g transform="translate(0 -10)">{children}</g>
    </g>
  );
}

/** Bars of a sorting picture. `sorted` bars are green, the rest blue; `pointer` puts a marker under one bar. */
export function Bars({ values, sorted = 0, w = 16, gap = 6, max = 80, pointer, animate }:
  { values: number[]; sorted?: number; w?: number; gap?: number; max?: number; pointer?: number; animate?: boolean }) {
  const total = values.length * w + (values.length - 1) * gap;
  const top = Math.max(...values);
  return (
    <g>
      {values.map((v, i) => {
        const h = (v / top) * max;
        return (
          <rect key={i} className={animate ? "bar-grow" : undefined} style={animate ? { animationDelay: `${0.15 * i}s` } : undefined}
            x={-total / 2 + i * (w + gap)} y={max / 2 - h} width={w} height={h} rx={4} fill={i < sorted ? C.green : C.blue} />
        );
      })}
      {pointer != null && (
        <path className={animate ? "scan" : undefined} d={`M ${-total / 2 + pointer * (w + gap) + w / 2} ${max / 2 + 8} l -7 11 h 14 z`} fill={C.orange} />
      )}
    </g>
  );
}
