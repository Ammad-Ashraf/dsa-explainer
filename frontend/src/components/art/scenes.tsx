// Whole illustrations for the home and library pages. Objects float (see .float); placement stays in At.
import { At, Bars, Block, C, Device, Float, Label } from "./primitives";
import { Badge, GraphToken, Helper, QueueToken, StackToken, TreeToken, VerifiedBadge, VoiceBubble } from "./tokens";

/** The opening: the helper beside a phone that is sorting, surrounded by what the app teaches. */
export function HeroArt() {
  return (
    <svg viewBox="0 0 424 424" role="img" aria-label="A friendly node character beside a phone playing a sorting lesson, surrounded by a stack, a queue, a tree, a graph, a verified badge and a voice bubble">
      <At x={248} y={214} rotate={10}>
        <Float slow>
          <Device>
            <Bars values={[2, 3, 5, 7, 4, 6]} sorted={3} pointer={4} animate />
            <rect x={-44} y={60} width={88} height={8} rx={4} fill={C.blue} opacity={0.3} />
            <rect x={-44} y={60} width={52} height={8} rx={4} fill={C.blue} className="progress" />
          </Device>
        </Float>
      </At>
      <At x={104} y={302}><Float delay={0.4}><Helper r={58} /></Float></At>
      <At x={80} y={118} rotate={-10}><Float delay={0.8}><StackToken /></Float></At>
      <At x={205} y={58} rotate={-6}><Float delay={1.6}><GraphToken /></Float></At>
      <At x={355} y={72} rotate={8}><Float delay={1.2}><TreeToken /></Float></At>
      <At x={360} y={360} rotate={-8}><Float delay={2}><QueueToken /></Float></At>
      <At x={48} y={208} rotate={-8}><Float delay={2.4}><VerifiedBadge size={0.75} /></Float></At>
      <At x={372} y={208} rotate={6}><Float delay={0.2}><VoiceBubble /></Float></At>
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

/** The closing landscape: a white valley cut into green, with the finished lesson in the middle. */
export function Valley() {
  return (
    <svg viewBox="0 0 1440 360" preserveAspectRatio="xMidYMax slice" className="valley-art" aria-hidden="true">
      <rect width={1440} height={360} fill={C.green} />
      <path d="M 0 0 H 1440 V 110 C 1230 110 1150 320 720 320 C 290 320 210 110 0 110 Z" fill={C.white} />
      <At x={720} y={196} rotate={-6}>
        <Float slow>
          <Device w={164} h={226}>
            <Bars values={[1, 2, 3, 4, 5, 6]} sorted={6} />
            <g transform="translate(0 64)"><VerifiedBadge size={0.45} /></g>
          </Device>
        </Float>
      </At>
      <At x={548} y={214} rotate={-12}><Float delay={0.5}><Badge kind="star" r={28} /></Float></At>
      <At x={884} y={226} rotate={10}><Float delay={1.1}><VerifiedBadge size={0.8} /></Float></At>
      <At x={452} y={170} rotate={-8}><Float delay={1.6}><StackToken /></Float></At>
      <At x={1000} y={168} rotate={8}><Float delay={0.9}><TreeToken /></Float></At>
      <At x={830} y={300}><Float delay={0.3}><Helper r={40} /></Float></At>
    </svg>
  );
}
