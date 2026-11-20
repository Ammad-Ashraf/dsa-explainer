// Original illustrations, built the way docs/design/design-system.md describes: flat rounded shapes,
// a darker offset "side face" instead of blurred shadows, tilted objects floating on white.
import type { ReactNode } from "react";

const C = {
  green: "#58cc02", greenSide: "#46a302", blue: "#1cb0f6", blueSide: "#1899d6", yellow: "#ffc800", yellowSide: "#e5a800",
  pink: "#ff86d0", pinkSide: "#e66bb6", purple: "#ce82ff", purpleSide: "#a568cc", orange: "#ff9600", orangeSide: "#e08400",
  ink: "#4b4b4b", sky: "#ddf4ff", white: "#ffffff", rule: "#e5e5e5",
};

/** A shape drawn twice: a darker copy shifted down (the side face), then the face. */
function Raised({ children, side, dy = 5 }: { children: (fill: string) => ReactNode; side: string; dy?: number }) {
  return (
    <>
      <g transform={`translate(0 ${dy})`}>{children(side)}</g>
      {children("")}
    </>
  );
}

/** The helper: a friendly round node with a "next" pointer. */
export function Helper({ x = 0, y = 0, r = 60, mood = "happy" }: { x?: number; y?: number; r?: number; mood?: "happy" | "wow" }) {
  const e = r * 0.28;
  return (
    <g transform={`translate(${x} ${y})`}>
      <path d={`M ${r * 0.9} ${r * 0.1} L ${r * 1.7} ${r * 0.1}`} stroke={C.ink} strokeWidth={r * 0.11} strokeLinecap="round" />
      <path d={`M ${r * 1.5} ${-r * 0.12} L ${r * 1.75} ${r * 0.1} L ${r * 1.5} ${r * 0.32}`} stroke={C.ink} strokeWidth={r * 0.11}
        strokeLinecap="round" strokeLinejoin="round" fill="none" />
      <circle cx={0} cy={r * 0.12} r={r} fill={C.greenSide} />
      <circle cx={0} cy={0} r={r} fill={C.green} />
      <ellipse cx={-r * 0.35} cy={-r * 0.48} rx={r * 0.22} ry={r * 0.12} fill="#89e219" transform={`rotate(-25 ${-r * 0.35} ${-r * 0.48})`} />
      <circle cx={-r * 0.36} cy={-r * 0.05} r={e} fill={C.white} />
      <circle cx={r * 0.36} cy={-r * 0.05} r={e} fill={C.white} />
      <circle cx={-r * 0.3} cy={-r * 0.02} r={e * 0.52} fill={C.ink} />
      <circle cx={r * 0.42} cy={-r * 0.02} r={e * 0.52} fill={C.ink} />
      {mood === "happy" ? (
        <path d={`M ${-r * 0.32} ${r * 0.32} Q 0 ${r * 0.62} ${r * 0.32} ${r * 0.32}`} stroke={C.white} strokeWidth={r * 0.1} fill="none" strokeLinecap="round" />
      ) : (
        <ellipse cx={0} cy={r * 0.42} rx={r * 0.14} ry={r * 0.17} fill={C.ink} />
      )}
      <circle cx={-r * 0.62} cy={r * 0.25} r={r * 0.1} fill="#ffb3d9" opacity={0.8} />
      <circle cx={r * 0.62} cy={r * 0.25} r={r * 0.1} fill="#ffb3d9" opacity={0.8} />
    </g>
  );
}

function Plates({ x, y, rotate = 0 }: { x: number; y: number; rotate?: number }) {
  return (
    <g transform={`translate(${x} ${y}) rotate(${rotate})`}>
      {[0, 1, 2].map((i) => (
        <Raised key={i} side={C.yellowSide} dy={4}>
          {(side) => <rect x={-34 + i * 4} y={-i * 17} width={68 - i * 8} height={13} rx={6} fill={side || C.yellow} />}
        </Raised>
      ))}
    </g>
  );
}

function Tree({ x, y, rotate = 0, scale = 1 }: { x: number; y: number; rotate?: number; scale?: number }) {
  const nodes: [number, number][] = [[0, -26], [-22, 6], [22, 6], [-34, 36], [-8, 36]];
  return (
    <g transform={`translate(${x} ${y}) rotate(${rotate}) scale(${scale})`}>
      {[[0, 1], [0, 2], [1, 3], [1, 4]].map(([a, b], i) => (
        <line key={i} x1={nodes[a][0]} y1={nodes[a][1]} x2={nodes[b][0]} y2={nodes[b][1]} stroke={C.purpleSide} strokeWidth={5} strokeLinecap="round" />
      ))}
      {nodes.map(([nx, ny], i) => (
        <Raised key={i} side={C.purpleSide} dy={3}>
          {(side) => <circle cx={nx} cy={ny} r={10} fill={side || C.purple} />}
        </Raised>
      ))}
    </g>
  );
}

function Pins({ x, y, rotate = 0 }: { x: number; y: number; rotate?: number }) {
  const pts: [number, number][] = [[-26, 10], [6, -22], [30, 14]];
  return (
    <g transform={`translate(${x} ${y}) rotate(${rotate})`}>
      <path d="M -26 10 L 6 -22 L 30 14 Z" stroke={C.blueSide} strokeWidth={5} fill="none" strokeLinejoin="round" />
      {pts.map(([px, py], i) => (
        <Raised key={i} side={C.blueSide} dy={3}>
          {(side) => <circle cx={px} cy={py} r={11} fill={side || C.blue} />}
        </Raised>
      ))}
    </g>
  );
}

function Tickets({ x, y, rotate = 0 }: { x: number; y: number; rotate?: number }) {
  return (
    <g transform={`translate(${x} ${y}) rotate(${rotate})`}>
      {[0, 1, 2].map((i) => (
        <Raised key={i} side={C.pinkSide} dy={4}>
          {(side) => <rect x={-40 + i * 28} y={-12} width={22} height={24} rx={6} fill={side || C.pink} />}
        </Raised>
      ))}
    </g>
  );
}

function Coin({ x, y, r = 22, rotate = 0, glyph = "check" }: { x: number; y: number; r?: number; rotate?: number; glyph?: "check" | "star" | "q" }) {
  return (
    <g transform={`translate(${x} ${y}) rotate(${rotate})`}>
      <circle cx={0} cy={5} r={r} fill={glyph === "star" ? C.yellowSide : glyph === "q" ? C.orangeSide : C.greenSide} />
      <circle cx={0} cy={0} r={r} fill={glyph === "star" ? C.yellow : glyph === "q" ? C.orange : C.green} />
      {glyph === "check" && <path d={`M ${-r * 0.42} 0 L ${-r * 0.1} ${r * 0.32} L ${r * 0.45} ${-r * 0.3}`} stroke={C.white} strokeWidth={r * 0.22} fill="none" strokeLinecap="round" strokeLinejoin="round" />}
      {glyph === "star" && <path d={star(0, 0, r * 0.55, r * 0.24)} fill={C.white} />}
      {glyph === "q" && <text x={0} y={r * 0.36} textAnchor="middle" fontSize={r * 1.1} fontWeight={800} fill={C.white} fontFamily="Nunito, sans-serif">?</text>}
    </g>
  );
}

function star(cx: number, cy: number, outer: number, inner: number) {
  const pts = Array.from({ length: 10 }, (_, i) => {
    const r = i % 2 ? inner : outer;
    const a = (Math.PI / 5) * i - Math.PI / 2;
    return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`;
  });
  return `M ${pts.join(" L ")} Z`;
}

function Device({ x, y, w = 150, h = 210, rotate = 0, children }: { x: number; y: number; w?: number; h?: number; rotate?: number; children?: ReactNode }) {
  return (
    <g transform={`translate(${x} ${y}) rotate(${rotate})`}>
      <rect x={-w / 2} y={-h / 2 + 8} width={w} height={h} rx={22} fill="#333" />
      <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={22} fill={C.ink} />
      <rect x={-w / 2 + 10} y={-h / 2 + 12} width={w - 20} height={h - 30} rx={14} fill={C.sky} />
      <g transform={`translate(0 ${-6})`}>{children}</g>
    </g>
  );
}

function Bars({ values, w = 16, gap = 6, max = 80, colours }: { values: number[]; w?: number; gap?: number; max?: number; colours?: string[] }) {
  const total = values.length * w + (values.length - 1) * gap;
  const top = Math.max(...values);
  return (
    <g>
      {values.map((v, i) => {
        const h = (v / top) * max;
        return <rect key={i} x={-total / 2 + i * (w + gap)} y={max / 2 - h} width={w} height={h} rx={4} fill={colours?.[i] ?? C.blue} />;
      })}
    </g>
  );
}

export function HeroArt() {
  return (
    <svg viewBox="0 0 424 424" role="img" aria-label="A friendly node character next to a phone playing a sorting animation, with floating stacks, trees and graphs">
      <Device x={250} y={215} rotate={12}>
        <Bars values={[2, 4, 3, 6, 5, 8]} colours={[C.green, C.green, C.green, C.blue, C.blue, C.blue]} />
        <rect x={-40} y={58} width={80} height={10} rx={5} fill={C.blue} opacity={0.35} />
      </Device>
      <Helper x={108} y={300} r={66} />
      <Plates x={92} y={118} rotate={-14} />
      <Tree x={360} y={70} rotate={10} />
      <Pins x={210} y={56} rotate={-8} />
      <Tickets x={366} y={350} rotate={-12} />
      <Coin x={60} y={200} r={20} rotate={-10} />
      <Coin x={330} y={160} r={16} rotate={14} glyph="star" />
    </svg>
  );
}

export type BenefitArtKind = "verify" | "voice" | "quiz" | "change" | "library";

export function BenefitArt({ kind }: { kind: BenefitArtKind }) {
  return (
    <svg viewBox="0 0 530 420" role="img" aria-hidden="true">
      {kind === "verify" && (
        <>
          <Device x={230} y={210} w={230} h={190} rotate={-6}>
            <Bars values={[3, 5, 2, 7, 4]} w={22} gap={10} max={90} colours={[C.blue, C.green, C.blue, C.blue, C.blue]} />
          </Device>
          <g transform="translate(372 150) rotate(12)">
            <circle cx={0} cy={6} r={58} fill={C.greenSide} />
            <circle cx={0} cy={0} r={58} fill={C.green} />
            <path d="M -24 0 L -6 18 L 26 -16" stroke={C.white} strokeWidth={13} fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </g>
          <Helper x={110} y={318} r={48} mood="wow" />
          <Coin x={440} y={320} r={18} glyph="star" rotate={-8} />
          <Pins x={110} y={92} rotate={10} />
        </>
      )}
      {kind === "voice" && (
        <>
          <g transform="translate(265 230) rotate(-4)">
            <rect x={-150} y={-88} width={300} height={190} rx={18} fill="#333" />
            <rect x={-150} y={-96} width={300} height={190} rx={18} fill={C.ink} />
            <rect x={-136} y={-82} width={272} height={160} rx={10} fill={C.sky} />
            <rect x={-185} y={94} width={370} height={22} rx={11} fill="#333" />
            <rect x={-185} y={90} width={370} height={22} rx={11} fill="#5f5f5f" />
            <Helper x={-20} y={0} r={44} />
          </g>
          {[0, 1, 2].map((i) => (
            <path key={i} d={`M ${400 + i * 26} ${120 - i * 12} q ${24 + i * 6} ${50 + i * 14} 0 ${100 + i * 26}`} stroke={C.blue} strokeWidth={10} fill="none" strokeLinecap="round" opacity={1 - i * 0.25} />
          ))}
          <Coin x={95} y={110} r={22} glyph="star" rotate={-12} />
          <Plates x={110} y={370} rotate={8} />
        </>
      )}
      {kind === "quiz" && (
        <>
          <g transform="translate(250 215) rotate(5)">
            <rect x={-150} y={-122} width={300} height={250} rx={24} fill="#d0d0d0" />
            <rect x={-150} y={-130} width={300} height={250} rx={24} fill={C.white} stroke={C.rule} strokeWidth={4} />
            <rect x={-110} y={-100} width={220} height={18} rx={9} fill={C.rule} />
            {["A", "B", "C", "D"].map((l, i) => (
              <g key={l} transform={`translate(${i % 2 ? 60 : -60} ${-30 + Math.floor(i / 2) * 70})`}>
                <rect x={-50} y={-24} width={100} height={52} rx={12} fill={i === 1 ? "#f1ffe5" : C.white} stroke={i === 1 ? C.green : C.rule} strokeWidth={4} />
                <text x={0} y={10} textAnchor="middle" fontSize={26} fontWeight={800} fill={i === 1 ? C.green : "#afafaf"} fontFamily="Nunito, sans-serif">{l}</text>
              </g>
            ))}
          </g>
          <Coin x={420} y={110} r={30} glyph="q" rotate={12} />
          <Coin x={108} y={330} r={26} glyph="check" rotate={-10} />
          <Tickets x={110} y={100} rotate={-10} />
        </>
      )}
      {kind === "change" && (
        <>
          <g transform="translate(265 200) rotate(-5)">
            <rect x={-230} y={-62} width={460} height={132} rx={18} fill="#333" />
            <rect x={-230} y={-70} width={460} height={132} rx={18} fill={C.ink} />
            {[0, 1, 2, 3].map((i) => (
              <rect key={i} x={-212 + i * 108} y={-52} width={92} height={96} rx={10} fill={i === 2 ? "#f1ffe5" : C.sky} stroke={i === 2 ? C.green : "none"} strokeWidth={5} />
            ))}
            {[...Array(12)].map((_, i) => <rect key={i} x={-218 + i * 38} y={52} width={18} height={8} rx={4} fill="#666" />)}
            <g transform="translate(-4 -4)"><Bars values={[2, 3, 5]} w={14} gap={6} max={56} colours={[C.green, C.green, C.green]} /></g>
          </g>
          <path d="M 290 330 q 60 40 120 -10" stroke={C.blue} strokeWidth={9} fill="none" strokeLinecap="round" />
          <path d="M 395 300 l 18 18 l -24 10" stroke={C.blue} strokeWidth={9} fill="none" strokeLinecap="round" strokeLinejoin="round" />
          <Helper x={190} y={350} r={44} />
          <Coin x={450} y={90} r={20} glyph="star" rotate={10} />
        </>
      )}
      {kind === "library" && (
        <>
          {[[-130, -8, C.yellow, C.yellowSide], [-40, 4, C.blue, C.blueSide], [50, -6, C.purple, C.purpleSide], [140, 8, C.pink, C.pinkSide]].map(([dx, rot, face, side], i) => (
            <g key={i} transform={`translate(${265 + (dx as number)} 230) rotate(${rot})`}>
              <rect x={-38} y={-118} width={76} height={236} rx={12} fill={side as string} />
              <rect x={-38} y={-126} width={76} height={236} rx={12} fill={face as string} />
              <rect x={-22} y={-96} width={44} height={10} rx={5} fill={C.white} opacity={0.7} />
            </g>
          ))}
          <Helper x={430} y={340} r={46} />
          <Coin x={90} y={360} r={20} glyph="check" />
        </>
      )}
    </svg>
  );
}

export type StageIconKind = "plan" | "verify" | "quiz" | "voice" | "draw" | "join";

export function StageIcon({ kind, size = 56 }: { kind: StageIconKind; size?: number }) {
  const face = { plan: C.yellow, verify: C.green, quiz: C.orange, voice: C.blue, draw: C.purple, join: C.pink }[kind];
  const side = { plan: C.yellowSide, verify: C.greenSide, quiz: C.orangeSide, voice: C.blueSide, draw: C.purpleSide, join: C.pinkSide }[kind];
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <rect x={4} y={9} width={56} height={52} rx={16} fill={side} />
      <rect x={4} y={4} width={56} height={52} rx={16} fill={face} />
      <g stroke={C.white} strokeWidth={5} fill="none" strokeLinecap="round" strokeLinejoin="round">
        {kind === "plan" && <><path d="M 20 20 h 24 M 20 30 h 24 M 20 40 h 14" /></>}
        {kind === "verify" && <path d="M 19 31 l 9 9 l 17 -18" />}
        {kind === "quiz" && <><path d="M 25 22 q 7 -8 14 0 q 4 7 -7 12 v 5" /><circle cx={32} cy={46} r={1.5} fill={C.white} /></>}
        {kind === "voice" && <path d="M 18 30 v 0 M 25 22 v 16 M 32 16 v 28 M 39 22 v 16 M 46 30 v 0" />}
        {kind === "draw" && <><circle cx={23} cy={24} r={6} /><rect x={30} y={30} width={14} height={14} rx={3} /><path d="M 20 44 l 6 -9 l 6 9 z" /></>}
        {kind === "join" && <><rect x={16} y={18} width={32} height={22} rx={4} /><path d="M 16 46 h 32" /></>}
      </g>
    </svg>
  );
}

/** Colourful category emblems for the rail and the library (36 x 28). */
export function Emblem({ category, size = 36 }: { category: string; size?: number }) {
  const h = (size * 28) / 36;
  const draw: Record<string, ReactNode> = {
    linear: (<>{[0, 1, 2].map((i) => <rect key={i} x={6} y={18 - i * 7} width={24} height={5} rx={2.5} fill={[C.yellow, C.orange, C.yellowSide][i]} />)}</>),
    trees: (<><path d="M 18 6 L 9 18 M 18 6 L 27 18" stroke={C.purpleSide} strokeWidth={2.5} /><circle cx={18} cy={6} r={4.5} fill={C.purple} /><circle cx={9} cy={19} r={4.5} fill={C.purple} /><circle cx={27} cy={19} r={4.5} fill={C.purple} /></>),
    graphs: (<><path d="M 7 20 L 18 6 L 29 20 Z" stroke={C.blueSide} strokeWidth={2.5} fill="none" /><circle cx={7} cy={20} r={4.5} fill={C.blue} /><circle cx={18} cy={6} r={4.5} fill={C.blue} /><circle cx={29} cy={20} r={4.5} fill={C.blue} /></>),
    sorting: (<>{[6, 10, 14, 19].map((hh, i) => <rect key={i} x={5 + i * 7} y={24 - hh} width={5} height={hh} rx={2} fill={i < 2 ? C.green : C.greenSide} />)}</>),
    searching: (<><circle cx={15} cy={12} r={7} stroke={C.orange} strokeWidth={3.5} fill="none" /><path d="M 20 17 L 28 25" stroke={C.orangeSide} strokeWidth={4} strokeLinecap="round" /></>),
    hashing: (<><path d="M 13 5 L 10 24 M 23 5 L 20 24 M 7 11 H 29 M 6 18 H 28" stroke={C.pink} strokeWidth={3.5} strokeLinecap="round" /></>),
    dp: (<>{[0, 1, 2].map((r) => [0, 1, 2].map((c) => <rect key={`${r}${c}`} x={7 + c * 8} y={3 + r * 8} width={6} height={6} rx={1.5} fill={r + c < 3 ? C.blue : C.rule} />))}</>),
  };
  return (
    <svg width={size} height={h} viewBox="0 0 36 28" aria-hidden="true" className="emblem">
      {draw[category] ?? draw.linear}
    </svg>
  );
}

/** The closing landscape: a white valley cut into green, with the finished lesson in the middle. */
export function Valley() {
  return (
    <svg viewBox="0 0 1440 360" preserveAspectRatio="xMidYMax slice" style={{ width: "100%", height: "auto", minHeight: 220 }} aria-hidden="true">
      <rect x={0} y={0} width={1440} height={360} fill={C.green} />
      <path d="M 0 0 H 1440 V 120 C 1220 120 1160 330 720 330 C 280 330 220 120 0 120 Z" fill={C.white} />
      <path d="M 0 150 C 150 110 260 170 330 230 L 0 360 Z" fill={C.greenSide} opacity={0.5} />
      <path d="M 1440 150 C 1290 110 1180 170 1110 230 L 1440 360 Z" fill={C.greenSide} opacity={0.5} />
      <g transform="translate(720 200)">
        <Device x={0} y={0} w={170} h={230} rotate={-8}>
          <Bars values={[1, 2, 3, 4, 5, 6]} colours={Array(6).fill(C.green)} />
        </Device>
      </g>
      <Coin x={540} y={210} r={30} glyph="star" rotate={-12} />
      <Coin x={900} y={200} r={34} glyph="check" rotate={10} />
      <Tree x={470} y={300} rotate={-6} scale={0.9} />
      <Pins x={980} y={300} rotate={8} />
      <Plates x={1060} y={180} rotate={14} />
      <Tickets x={370} y={190} rotate={-14} />
      <Helper x={830} y={300} r={44} />
    </svg>
  );
}
