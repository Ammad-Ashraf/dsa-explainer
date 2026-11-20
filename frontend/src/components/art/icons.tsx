// Icons for the pipeline stages and emblems for the algorithm families.
import type { ReactNode } from "react";
import { C } from "./primitives";

export type StageIconKind = "plan" | "verify" | "quiz" | "voice" | "draw" | "join";

const STAGE_COLOURS: Record<StageIconKind, [string, string]> = {
  plan: [C.yellow, C.yellowSide], verify: [C.green, C.greenSide], quiz: [C.orange, C.orangeSide],
  voice: [C.blue, C.blueSide], draw: [C.purple, C.purpleSide], join: [C.pink, C.pinkSide],
};

export function StageIcon({ kind, size = 56 }: { kind: StageIconKind; size?: number }) {
  const [face, side] = STAGE_COLOURS[kind];
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <rect x={4} y={9} width={56} height={52} rx={16} fill={side} />
      <rect x={4} y={4} width={56} height={52} rx={16} fill={face} />
      <g stroke={C.white} strokeWidth={4.5} fill="none" strokeLinecap="round" strokeLinejoin="round">
        {kind === "plan" && (<><rect x={19} y={15} width={26} height={33} rx={4} /><path d="M 26 15 v -3 h 12 v 3 M 25 26 h 14 M 25 33 h 14 M 25 40 h 8" /></>)}
        {kind === "verify" && <path d="M 19 31 l 9 9 l 17 -18" />}
        {kind === "quiz" && (<><path d="M 25 22 q 7 -9 14 0 q 4 7 -7 12 v 5" /><circle cx={32} cy={46} r={1.5} fill={C.white} /></>)}
        {kind === "voice" && <path d="M 18 30 v 0 M 25 22 v 16 M 32 15 v 30 M 39 22 v 16 M 46 30 v 0" />}
        {kind === "draw" && (<><circle cx={23} cy={23} r={6} /><rect x={30} y={29} width={14} height={14} rx={3} /><path d="M 18 44 l 6 -9 l 6 9 z" /></>)}
        {kind === "join" && (<><rect x={15} y={17} width={34} height={24} rx={4} /><path d="M 15 47 h 34 M 29 24 l 7 5 l -7 5 z" /></>)}
      </g>
    </svg>
  );
}

const EMBLEMS: Record<string, ReactNode> = {
  linear: [0, 1, 2].map((i) => <rect key={i} x={7} y={19 - i * 7} width={22} height={5} rx={2.5} fill={[C.yellowSide, C.orange, C.yellow][i]} />),
  trees: (<><path d="M 18 6 L 9 18 M 18 6 L 27 18" stroke={C.purpleSide} strokeWidth={2.5} /><circle cx={18} cy={6} r={4.5} fill={C.purple} /><circle cx={9} cy={19} r={4.5} fill={C.purple} /><circle cx={27} cy={19} r={4.5} fill={C.purple} /></>),
  graphs: (<><path d="M 7 20 L 18 6 L 29 20 Z" stroke={C.blueSide} strokeWidth={2.5} fill="none" /><circle cx={7} cy={20} r={4.5} fill={C.blue} /><circle cx={18} cy={6} r={4.5} fill={C.orange} /><circle cx={29} cy={20} r={4.5} fill={C.blue} /></>),
  sorting: [6, 10, 14, 19].map((h, i) => <rect key={i} x={5 + i * 7} y={24 - h} width={5} height={h} rx={2} fill={i < 2 ? C.green : C.blue} />),
  searching: (<><circle cx={15} cy={12} r={7} stroke={C.orange} strokeWidth={3.5} fill="none" /><path d="M 20 17 L 28 25" stroke={C.orangeSide} strokeWidth={4} strokeLinecap="round" /></>),
  hashing: <path d="M 13 5 L 10 24 M 23 5 L 20 24 M 7 11 H 29 M 6 18 H 28" stroke={C.pink} strokeWidth={3.5} strokeLinecap="round" />,
  dp: [0, 1, 2].flatMap((r) => [0, 1, 2].map((c) => <rect key={`${r}${c}`} x={7 + c * 8} y={3 + r * 8} width={6} height={6} rx={1.5} fill={r + c < 3 ? C.blue : C.rule} />)),
};

/** Colourful category emblems for the rail and the library (36 x 28). */
export function Emblem({ category, size = 36 }: { category: string; size?: number }) {
  return (
    <svg width={size} height={(size * 28) / 36} viewBox="0 0 36 28" aria-hidden="true" className="emblem">
      {EMBLEMS[category] ?? EMBLEMS.linear}
    </svg>
  );
}
