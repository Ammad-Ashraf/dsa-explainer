// Small, recognisable symbols of what the app teaches and promises. Each is drawn around (0, 0).
import { C, Block, Dot, Label, starPath } from "./primitives";

/** The helper: a friendly graph node with two little edges for arms. */
export function Helper({ r = 60, mood = "happy", arms = true }: { r?: number; mood?: "happy" | "wow"; arms?: boolean }) {
  const e = r * 0.27;
  return (
    <g className="helper">
      {/* edges to neighbouring nodes, like arms */}
      {arms && <>
      <path d={`M ${-r * 0.9} ${r * 0.35} L ${-r * 1.45} ${r * 0.75}`} stroke={C.ink} strokeWidth={r * 0.1} strokeLinecap="round" />
      <path d={`M ${r * 0.9} ${r * 0.35} L ${r * 1.45} ${r * 0.75}`} stroke={C.ink} strokeWidth={r * 0.1} strokeLinecap="round" />
      <circle cx={-r * 1.5} cy={r * 0.8} r={r * 0.17} fill={C.yellow} stroke={C.ink} strokeWidth={r * 0.06} />
      <circle cx={r * 1.5} cy={r * 0.8} r={r * 0.17} fill={C.blue} stroke={C.ink} strokeWidth={r * 0.06} />
      </>}
      <circle cx={0} cy={r * 0.12} r={r} fill={C.greenSide} />
      <circle cx={0} cy={0} r={r} fill={C.green} />
      <ellipse cx={-r * 0.38} cy={-r * 0.55} rx={r * 0.24} ry={r * 0.12} fill={C.greenLight} transform={`rotate(-25 ${-r * 0.38} ${-r * 0.55})`} />
      {/* The blink is an SVG animation, not a CSS scale: a scaled CSS layer inside the floating helper is
          rasterised once and stretched, which looked blurry. SVG re-draws the vector on every frame. */}
      <g transform={`translate(0 ${-r * 0.06})`}>
        <g>
          <animateTransform attributeName="transform" type="scale" dur="4.5s" repeatCount="indefinite"
            keyTimes="0;0.92;0.945;0.975;1" values="1 1;1 1;1 0.12;1 1;1 1" />
          <g transform={`translate(0 ${r * 0.06})`}>
            <ellipse cx={-r * 0.36} cy={-r * 0.06} rx={e} ry={e * 1.12} fill={C.white} />
            <ellipse cx={r * 0.36} cy={-r * 0.06} rx={e} ry={e * 1.12} fill={C.white} />
            <circle cx={-r * 0.3} cy={-r * 0.02} r={e * 0.55} fill={C.ink} />
            <circle cx={r * 0.42} cy={-r * 0.02} r={e * 0.55} fill={C.ink} />
            <circle cx={-r * 0.25} cy={-r * 0.1} r={e * 0.18} fill={C.white} />
            <circle cx={r * 0.47} cy={-r * 0.1} r={e * 0.18} fill={C.white} />
          </g>
        </g>
      </g>
      {mood === "happy" ? (
        <path d={`M ${-r * 0.3} ${r * 0.34} Q 0 ${r * 0.62} ${r * 0.3} ${r * 0.34}`} stroke={C.white} strokeWidth={r * 0.1} fill="none" strokeLinecap="round" />
      ) : (
        <ellipse cx={0} cy={r * 0.44} rx={r * 0.13} ry={r * 0.16} fill={C.ink} />
      )}
      <circle cx={-r * 0.64} cy={r * 0.26} r={r * 0.1} fill="#ffb3d9" opacity={0.85} />
      <circle cx={r * 0.64} cy={r * 0.26} r={r * 0.1} fill="#ffb3d9" opacity={0.85} />
    </g>
  );
}

/** A stack of plates with a "push" arrow coming down onto the top. */
export function StackToken() {
  return (
    <g>
      <path d="M 0 -64 v 16" stroke={C.orange} strokeWidth={6} strokeLinecap="round" />
      <path d="M -9 -52 L 0 -42 L 9 -52" stroke={C.orange} strokeWidth={6} fill="none" strokeLinecap="round" strokeLinejoin="round" />
      {[0, 1, 2].map((i) => (
        <Block key={i} x={-34} y={-i * 17 - 6} w={68} h={13} r={6} face={C.yellow} side={C.yellowSide} dy={4} />
      ))}
    </g>
  );
}

/** A queue of tickets with an arrow running through them: in at the back, out at the front. */
export function QueueToken() {
  return (
    <g>
      {[0, 1, 2].map((i) => (
        <Block key={i} x={-44 + i * 30} y={-13} w={24} h={26} r={6} face={C.pink} side={C.pinkSide} dy={4} />
      ))}
      <path d="M -58 24 H 54" stroke={C.ink} strokeWidth={5} strokeLinecap="round" />
      <path d="M 46 16 L 56 24 L 46 32" stroke={C.ink} strokeWidth={5} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </g>
  );
}

/** A small binary tree: a root, two children, four leaves. */
export function TreeToken() {
  const nodes: [number, number][] = [[0, -30], [-26, -2], [26, -2], [-38, 26], [-14, 26], [14, 26], [38, 26]];
  const edges = [[0, 1], [0, 2], [1, 3], [1, 4], [2, 5], [2, 6]];
  return (
    <g>
      {edges.map(([a, b], i) => (
        <line key={i} x1={nodes[a][0]} y1={nodes[a][1]} x2={nodes[b][0]} y2={nodes[b][1]} stroke={C.purpleSide} strokeWidth={4.5} strokeLinecap="round" />
      ))}
      {nodes.map(([x, y], i) => <Dot key={i} cx={x} cy={y} r={i === 0 ? 10 : 8.5} face={i === 0 ? C.purple : "#e0b3ff"} side={C.purpleSide} dy={3} />)}
    </g>
  );
}

/** A graph: four nodes, one of them being visited. */
export function GraphToken() {
  const pts: [number, number][] = [[-32, 14], [0, -24], [32, 10], [8, 34]];
  return (
    <g>
      <path d="M -32 14 L 0 -24 L 32 10 L 8 34 Z M 0 -24 L 8 34" stroke={C.blueSide} strokeWidth={4.5} fill="none" strokeLinejoin="round" />
      {pts.map(([x, y], i) => <Dot key={i} cx={x} cy={y} r={10} face={i === 1 ? C.orange : C.blue} side={i === 1 ? C.orangeSide : C.blueSide} dy={3} />)}
    </g>
  );
}

/** A shield with a tick: checked by running the real algorithm. */
export function VerifiedBadge({ size = 1 }: { size?: number }) {
  const shield = "M 0 -34 L 28 -24 V 2 C 28 20 14 31 0 38 C -14 31 -28 20 -28 2 V -24 Z";
  return (
    <g transform={`scale(${size})`}>
      <path d={shield} fill={C.greenSide} transform="translate(0 5)" />
      <path d={shield} fill={C.green} />
      <path d="M -12 2 L -3 11 L 14 -8" stroke={C.white} strokeWidth={7} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </g>
  );
}

/** A speech bubble with sound bars: the narration. */
export function VoiceBubble() {
  return (
    <g>
      <path d="M -34 -24 h 68 a 12 12 0 0 1 12 12 v 26 a 12 12 0 0 1 -12 12 h -40 l -14 12 v -12 h -14 a 12 12 0 0 1 -12 -12 v -26 a 12 12 0 0 1 12 -12 z" fill={C.blueSide} transform="translate(0 4)" />
      <path d="M -34 -24 h 68 a 12 12 0 0 1 12 12 v 26 a 12 12 0 0 1 -12 12 h -40 l -14 12 v -12 h -14 a 12 12 0 0 1 -12 -12 v -26 a 12 12 0 0 1 12 -12 z" fill={C.blue} />
      {[-18, -6, 6, 18].map((x, i) => {
        const h = [10, 22, 16, 8][i];
        const low = h * 0.4;
        // SVG-native animation (redrawn as vector each frame) rather than a CSS scale, which blurs when composited
        return (
          <rect key={x} x={x - 3} y={-h / 2 + 1} width={6} height={h} rx={3} fill={C.white}>
            <animate attributeName="height" values={`${h};${low};${h}`} dur="1.1s" begin={`${i * 0.15}s`} repeatCount="indefinite" />
            <animate attributeName="y" values={`${-h / 2 + 1};${-low / 2 + 1};${-h / 2 + 1}`} dur="1.1s" begin={`${i * 0.15}s`} repeatCount="indefinite" />
          </rect>
        );
      })}
    </g>
  );
}

/** A round badge: a star (well done) or a question mark (the quiz). */
export function Badge({ kind, r = 22 }: { kind: "star" | "question"; r?: number }) {
  const face = kind === "star" ? C.yellow : C.orange;
  const side = kind === "star" ? C.yellowSide : C.orangeSide;
  return (
    <g>
      <Dot cx={0} cy={0} r={r} face={face} side={side} dy={5} />
      {kind === "star" ? <path d={starPath(0, 0, r * 0.56, r * 0.24)} fill={C.white} /> : <Label x={0} y={r * 0.38} size={r * 1.1} fill={C.white}>?</Label>}
    </g>
  );
}
