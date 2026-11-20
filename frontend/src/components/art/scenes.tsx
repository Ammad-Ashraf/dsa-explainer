// Whole illustrations for the home and library pages. Objects float (see .float); placement stays in At.
import { At, Bars, Block, C, Float, Label } from "./primitives";
import { Badge, Helper, VerifiedBadge, VoiceBubble } from "./tokens";

/** The opening: one sorting lesson told as three step cards, each compared, swapped and checked, ending in "sorted";
    the voice bubble with moving sound bars says it is narrated, a shield says every step was checked by code. */
export function HeroArt() {
  type Step = { n: number; bars: number[]; hot: [number, number] | null; caption: string; done?: boolean };
  const steps: Step[] = [
    { n: 1, bars: [3, 1, 2], hot: [0, 1], caption: "3 > 1, swap them" },
    { n: 2, bars: [1, 3, 2], hot: [1, 2], caption: "3 > 2, swap them" },
    { n: 3, bars: [1, 2, 3], hot: null, caption: "sorted!", done: true },
  ];
  const place = [{ x: 108, y: 84, r: -4 }, { x: 206, y: 206, r: 2 }, { x: 304, y: 328, r: -3 }];
  const bx = (i: number) => -44 + i * 44; // bar centres
  return (
    <svg viewBox="0 0 424 424" role="img"
      aria-label="A sorting lesson as three step cards: compare and swap three and one, compare and swap three and two, then sorted. Each step has a green check. A voice bubble with moving sound bars shows the narration, and a shield shows every step was checked">
      {steps.map((st, i) => (
        <At key={st.n} x={place[i].x} y={place[i].y} rotate={place[i].r}>
          <Float slow delay={i * 0.6}>
            <Block x={-100} y={-62} w={200} h={124} r={22} face={C.white} side={st.done ? C.greenSide : C.rule} stroke={st.done ? C.green : C.rule} dy={6} />
            <Label x={-82} y={-38} size={12} fill={C.muted} anchor="start">STEP {st.n}</Label>
            <circle cx={78} cy={-42} r={12} fill={C.green} />
            <path d="M 72 -42 l 4.5 5 l 8 -10" stroke={C.white} strokeWidth={3.5} strokeLinecap="round" strokeLinejoin="round" fill="none" />
            {st.bars.map((v, k) => {
              const h = 12 + v * 13;
              const hot = st.hot && (k === st.hot[0] || k === st.hot[1]);
              const face = st.done ? C.green : hot ? C.orange : C.blue;
              const side = st.done ? C.greenSide : hot ? C.orangeSide : C.blueSide;
              return (
                <g key={k}>
                  <rect x={bx(k) - 15} y={30 - h + 4} width={30} height={h} rx={8} fill={side} />
                  <rect x={bx(k) - 15} y={30 - h} width={30} height={h} rx={8} fill={face} />
                  <Label x={bx(k)} y={30 - h + 20} size={16} fill={C.white}>{v}</Label>
                </g>
              );
            })}
            {st.hot && (() => {
              // from just above the first bar, up and over, down onto the second: the arrowhead touches its target
              const [from, to] = st.hot;
              const top = (k: number) => 30 - (12 + st.bars[k] * 13);
              const y1 = top(from) - 6, y2 = top(to) - 7, x1 = bx(from), x2 = bx(to);
              return (
                <g stroke={C.orange} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round" fill="none">
                  <path d={`M ${x1} ${y1} C ${x1} ${y1 - 18} ${x2} ${y1 - 18} ${x2} ${y2 - 4}`} />
                  <path d={`M ${x2 - 6} ${y2 - 9} L ${x2} ${y2} L ${x2 + 6} ${y2 - 9}`} />
                </g>
              );
            })()}
            <Label x={0} y={50} size={13} fill={st.done ? C.greenSide : C.ink}>{st.caption}</Label>
          </Float>
        </At>
      ))}

      {/* narrated video */}
      <At x={338} y={66}>
        <Float delay={0.4}><At x={0} y={0} scale={1.25}><VoiceBubble /></At></Float>
        <Label x={0} y={68} size={12} fill={C.blue}>NARRATED</Label>
      </At>

      {/* checked by code */}
      <At x={82} y={330} rotate={-6}>
        <Float delay={1}><VerifiedBadge size={1.15} /></Float>
        <Label x={0} y={62} size={12} fill={C.greenSide}>CHECKED BY CODE</Label>
      </At>

    </svg>
  );
}

/** "every step is checked": what the plan claims, set against what the real run shows. */
function VerifyScene() {
  return (
    <>
      <At x={150} y={190} rotate={-5}>
        <Block x={-95} y={-88} w={190} h={176} r={20} face={C.white} side={C.rule} stroke={C.rule} dy={7} />
        <Label x={0} y={-56} size={18} fill={C.muted}>THE PLAN SAYS</Label>
        <g transform="translate(0 6)"><Bars values={[3, 5, 2, 7]} w={24} gap={12} max={84} /></g>
      </At>
      <At x={378} y={190} rotate={5}>
        <Block x={-95} y={-88} w={190} h={176} r={20} face={C.white} side={C.rule} stroke={C.green} dy={7} />
        <Label x={0} y={-56} size={18} fill={C.green}>THE REAL RUN</Label>
        <g transform="translate(0 6)"><Bars values={[3, 5, 2, 7]} sorted={4} w={24} gap={12} max={84} /></g>
      </At>
      <At x={264} y={196}>
        <circle r={26} fill={C.white} stroke={C.rule} strokeWidth={4} />
        <Label x={0} y={11} size={32} fill={C.ink}>=</Label>
      </At>
      <At x={444} y={84}><Float><VerifiedBadge /></Float></At>
      <At x={262} y={346}><Float delay={0.6}><Helper r={44} mood="wow" /></Float></At>
    </>
  );
}

/** "a voice that lives on your laptop": a laptop speaking, with a home badge for "on this computer". */
function VoiceScene() {
  return (
    <>
      <At x={250} y={220} rotate={-3}>
        <rect x={-160} y={-102} width={320} height={200} rx={20} fill={C.inkSide} />
        <rect x={-160} y={-110} width={320} height={200} rx={20} fill={C.ink} />
        <rect x={-146} y={-96} width={292} height={168} rx={12} fill={C.blueWash} />
        <g transform="translate(-60 -10)"><Helper r={40} /></g>
        {[0, 1, 2, 3, 4, 5, 6].map((i) => {
          const h = [18, 40, 62, 44, 70, 34, 20][i];
          return <rect key={i} className="wave" style={{ animationDelay: `${i * 0.12}s` }} x={10 + i * 18} y={-10 - h / 2} width={10} height={h} rx={5} fill={C.blue} />;
        })}
        <rect x={-196} y={90} width={392} height={22} rx={11} fill="#5f5f5f" />
        <rect x={-196} y={94} width={392} height={22} rx={11} fill={C.inkSide} opacity={0.5} />
      </At>
      <At x={430} y={92}><Float delay={0.3}><VoiceBubble /></Float></At>
      <At x={84} y={96} rotate={-8}>
        <Float delay={1}>
          <Block x={-32} y={-28} w={64} h={60} r={14} face={C.green} side={C.greenSide} />
          <path d="M -16 6 L 0 -10 L 16 6 V 20 H -16 Z" fill={C.white} />
        </Float>
      </At>
    </>
  );
}

/** "quiz yourself": a question card with the right answer ticked. */
function QuizScene() {
  return (
    <>
      <At x={262} y={210} rotate={4}>
        <Block x={-160} y={-140} w={320} h={270} r={26} face={C.white} side={C.rule} stroke={C.rule} dy={8} />
        <rect x={-120} y={-108} width={240} height={16} rx={8} fill={C.rule} />
        <rect x={-120} y={-80} width={150} height={16} rx={8} fill={C.rule} />
        {["A", "B", "C", "D"].map((l, i) => {
          const right = i === 1;
          return (
            <g key={l} transform={`translate(${i % 2 ? 66 : -66} ${-14 + Math.floor(i / 2) * 76})`}>
              <Block x={-56} y={-28} w={112} h={56} r={14} face={right ? "#f1ffe5" : C.white} side={right ? C.green : C.rule} stroke={right ? C.green : C.rule} dy={4} />
              <Label x={right ? -14 : 0} y={10} size={26} fill={right ? C.green : C.muted}>{l}</Label>
              {right && <path d="M 8 0 l 8 8 l 16 -16" stroke={C.green} strokeWidth={6} fill="none" strokeLinecap="round" strokeLinejoin="round" />}
            </g>
          );
        })}
      </At>
      <At x={448} y={70} rotate={10}><Float><Badge kind="question" r={30} /></Float></At>
      <At x={64} y={86} rotate={-8}><Float delay={0.8}><Badge kind="star" r={24} /></Float></At>
      <At x={70} y={352}><Float delay={1.4}><Helper r={34} /></Float></At>
    </>
  );
}

/** "change any part": one scene of the film is redrawn, the others are reused. */
function ChangeScene() {
  return (
    <>
      <At x={265} y={190} rotate={-4}>
        <rect x={-235} y={-60} width={470} height={136} rx={20} fill={C.inkSide} />
        <rect x={-235} y={-68} width={470} height={136} rx={20} fill={C.ink} />
        {[0, 1, 2, 3].map((i) => {
          const redrawn = i === 2;
          return (
            <g key={i}>
              <rect x={-216 + i * 110} y={-50} width={94} height={100} rx={12} fill={redrawn ? "#f1ffe5" : C.blueWash} stroke={redrawn ? C.green : "none"} strokeWidth={5} />
              <g transform={`translate(${-169 + i * 110} 0)`}>
                <Bars values={[2, 4, 3, 5].slice(0, 2 + (i % 3))} sorted={redrawn ? 4 : 0} w={12} gap={6} max={redrawn ? 54 : 46} />
              </g>
              <Label x={-169 + i * 110} y={44} size={13} fill={redrawn ? C.green : C.muted}>{redrawn ? "REDRAWN" : "REUSED"}</Label>
            </g>
          );
        })}
        {[...Array(12)].map((_, i) => <rect key={i} x={-222 + i * 39} y={56} width={20} height={7} rx={3.5} fill="#666" />)}
      </At>
      <At x={288} y={64}>
        <Float delay={0.4}>
          <Block x={-112} y={-26} w={224} h={52} r={16} face={C.white} side={C.rule} stroke={C.rule} dy={4} />
          <Label x={0} y={7} size={18}>“slow down step 3”</Label>
        </Float>
      </At>
      <At x={118} y={340}><Float delay={1}><Helper r={42} /></Float></At>
      <At x={440} y={340} rotate={8}><Float delay={1.6}><Badge kind="star" r={22} /></Float></At>
    </>
  );
}

/** The library: a shelf of books, each spine marked with what it teaches. */
function LibraryScene() {
  const books = [
    { dx: -150, rot: -6, face: C.yellow, side: C.yellowSide, mark: "stack" },
    { dx: -55, rot: 3, face: C.purple, side: C.purpleSide, mark: "tree" },
    { dx: 40, rot: -3, face: C.blue, side: C.blueSide, mark: "graph" },
    { dx: 135, rot: 6, face: C.green, side: C.greenSide, mark: "bars" },
  ];
  return (
    <>
      <rect x={70} y={350} width={390} height={18} rx={9} fill={C.rule} />
      {books.map((b, i) => (
        <At key={i} x={265 + b.dx} y={232} rotate={b.rot}>
          <Block x={-40} y={-124} w={80} h={238} r={14} face={b.face} side={b.side} dy={7} />
          <rect x={-24} y={-100} width={48} height={10} rx={5} fill={C.white} opacity={0.75} />
          <g transform="translate(0 10)" fill={C.white} stroke={C.white}>
            {b.mark === "stack" && [0, 1, 2].map((k) => <rect key={k} x={-20} y={-k * 13} width={40} height={9} rx={4.5} stroke="none" />)}
            {b.mark === "tree" && <><path d="M 0 -18 L -16 6 M 0 -18 L 16 6" strokeWidth={4} /><circle cx={0} cy={-18} r={7} /><circle cx={-16} cy={8} r={7} /><circle cx={16} cy={8} r={7} /></>}
            {b.mark === "graph" && <><path d="M -18 10 L 0 -16 L 18 10 Z" strokeWidth={4} fill="none" /><circle cx={-18} cy={10} r={7} /><circle cx={0} cy={-16} r={7} /><circle cx={18} cy={10} r={7} /></>}
            {b.mark === "bars" && [10, 18, 26].map((h, k) => <rect key={k} x={-20 + k * 15} y={14 - h} width={10} height={h} rx={3} stroke="none" />)}
          </g>
        </At>
      ))}
      <At x={448} y={318}><Float><Helper r={40} /></Float></At>
    </>
  );
}

export type BenefitArtKind = "verify" | "voice" | "quiz" | "change" | "library";

export function BenefitArt({ kind }: { kind: BenefitArtKind }) {
  return (
    <svg viewBox="0 0 530 420" role="img" aria-hidden="true">
      {kind === "verify" && <VerifyScene />}
      {kind === "voice" && <VoiceScene />}
      {kind === "quiz" && <QuizScene />}
      {kind === "change" && <ChangeScene />}
      {kind === "library" && <LibraryScene />}
    </svg>
  );
}

/** The layered top edge of the footer: a white valley cut into green, with a darker lip and lighter bands that
    settle into the exact footer green, so no seam shows where the artwork ends. */
export function FooterLayers() {
  const valley = (side: number, dip: number) =>
    `M 0 0 H 1440 V ${side} C 1240 ${side} 1130 ${dip} 720 ${dip} C 310 ${dip} 200 ${side} 0 ${side} Z`;
  return (
    <svg viewBox="0 0 1440 260" preserveAspectRatio="none" className="footer-layers" aria-hidden="true">
      <rect width={1440} height={260} fill={C.green} />
      <path d={valley(150, 246)} fill={C.greenLight} opacity={0.14} />
      <path d={valley(125, 226)} fill={C.greenLight} opacity={0.2} />
      <path d={valley(100, 206)} fill={C.greenLight} opacity={0.28} />
      <path d={valley(70, 190)} fill={C.greenSide} />
      <path d={valley(70, 172)} fill={C.white} />
    </svg>
  );
}

/** The helper face on its own, floating above the closing call to action. */
export function CtaHelper() {
  return (
    <svg viewBox="-80 -80 160 160" className="cta-helper" aria-hidden="true">
      <Float><Helper r={50} /></Float>
    </svg>
  );
}
