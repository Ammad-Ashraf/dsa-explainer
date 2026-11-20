import { Link, useNavigate } from "react-router-dom";
import { algorithmById, api, useCatalog, usePlans } from "../api";
import { BenefitArt, type BenefitArtKind, CtaHelper, Emblem, FooterLayers, HeroArt, StageIcon, type StageIconKind } from "../components/art";
import { Reveal } from "../components/Reveal";
import { LinkButton } from "../components/ui";

const BENEFITS: { id: string; kind: BenefitArtKind; title: string; body: React.ReactNode }[] = [
  {
    id: "checked", kind: "verify", title: "every step is checked",
    body: (<>A language model writes the lesson plan, then we run every step on the real data structure. If the plan
      claims the wrong state, or the narration says something false, it goes back to be fixed. Nothing unchecked
      reaches the video. <a href="#how-it-works">See how it works</a>.</>),
  },
  {
    id: "local", kind: "voice", title: "a voice that lives on your laptop",
    body: <>The narration is spoken by a voice model running on your own computer, and the animation is timed to it,
      word for word. Your lessons never leave your machine.</>,
  },
  {
    id: "quiz", kind: "quiz", title: "quiz yourself",
    body: <>Every lesson ends with a short quiz. Each answer is worked out by running the operations, so the right
      answer is really right.</>,
  },
  {
    id: "change", kind: "change", title: "change any part",
    body: <>Say “slow down step 4” or “explain step 2 for a beginner”. Only the scenes you asked about are redrawn;
      everything else is reused, so changes take seconds.</>,
  },
];

const PIPELINE: { kind: StageIconKind; title: string; text: string; where: string }[] = [
  { kind: "plan", title: "Plan", text: "A language model writes the scenes, one operation each.", where: "your API key" },
  { kind: "verify", title: "Verify", text: "Every step runs on the real structure. Wrong plans go back.", where: "on your computer" },
  { kind: "quiz", title: "Quiz", text: "Questions whose answers are computed, not guessed.", where: "your API key" },
  { kind: "voice", title: "Voice", text: "Narration spoken by a local voice model.", where: "on your computer" },
  { kind: "draw", title: "Draw", text: "Scenes animated from the checked states only.", where: "on your computer" },
  { kind: "join", title: "Join", text: "Clips joined into one video, ready to replay.", where: "on your computer" },
];

const FAVOURITES = [
  { id: "bubble_sort", label: "Easy" },
  { id: "binary_search", label: "Intermediate" },
  { id: "dijkstra", label: "Advanced" },
];

const FAQ: [string, React.ReactNode][] = [
  ["Do I need an API key?", <>Only to make new lessons from your own topics. Every lesson in the <Link to="/library">library</Link> plays
    without one, and you can bring a free key (Google Gemini or Groq) or run a model locally with Ollama.</>],
  ["What runs on my computer?", <>Everything except the lesson planner: checking every step, the voice, the animation
    and the video. The planner and quiz writer call the language model you choose in Settings.</>],
  ["Which providers work?", <>Google Gemini, Anthropic Claude, OpenAI, Groq, OpenRouter, Ollama, LM Studio, or any
    server that speaks the OpenAI chat API.</>],
  ["How do you know a lesson is correct?", <>Every operation in the plan is run on a real implementation of the data
    structure. The planned state after each step, the facts in the narration and every quiz answer are compared with
    it. A plan that fails is sent back with the true state, and after four tries no video is made at all.</>],
  ["How long does a video take?", <>Usually one to two minutes on a laptop CPU for a two-minute lesson. You can start
    watching as soon as the first scene is drawn.</>],
  ["Is it free?", <>Yes. DSA Explainer is open source. The only possible cost is your language-model provider, and
    several have free tiers.</>],
];

export default function Home() {
  const { data: catalog } = useCatalog();
  const { data: plans } = usePlans();
  const navigate = useNavigate();
  // one favourite per level: easy, intermediate, advanced
  const popular = FAVOURITES
    .map(({ id, label }) => ({ plan: plans?.find((p) => p.id === id), label }))
    .filter((f): f is { plan: NonNullable<typeof f.plan>; label: string } => !!f.plan);

  async function watch(planId: string) {
    const job = await api.renderPlan(planId);
    navigate(`/studio/job/${job.id}`);
  }

  return (
    <>
      <section className="hero">
        <div className="container pair">
          <div className="art"><HeroArt /></div>
          <div className="copy">
            <h1 className="opening-heading">Watch any data structure come alive, one checked step at a time.</h1>
            <div className="actions">
              <LinkButton to="/studio" wide>Make a lesson</LinkButton>
              <LinkButton to="/library" variant="secondary" wide>Browse the library</LinkButton>
            </div>
          </div>
        </div>
      </section>

      <nav className="category-rail" aria-label="Algorithm families">
        <div className="inner">
          {Object.entries(catalog?.categories ?? {}).map(([id, title]) => (
            <Link key={id} to={`/library?category=${id}`}><Emblem category={id} />{title}</Link>
          ))}
        </div>
      </nav>

      <div className="container benefits">
        {BENEFITS.map((b, i) => (
          <Reveal as="section" key={b.id} id={b.id} className={`benefit${i % 2 ? " reverse" : ""}`}>
            <div className="copy">
              <h2 className="chapter-heading">{b.title}</h2>
              <p>{b.body}</p>
            </div>
            <div className="art"><BenefitArt kind={b.kind} /></div>
          </Reveal>
        ))}
      </div>

      <section className="sky-stage" id="how-it-works">
        <div className="container">
          <h2 className="display">six steps, one honest video</h2>
          <p className="sub lead">The language model only writes words. Everything you see is drawn from the real algorithm, on your own computer.</p>
          <div className="pipeline-tiles">
            {PIPELINE.map((s, i) => (
              <div key={s.kind} className="pipeline-tile">
                <span className="glow" style={{ animationDelay: `${i * 1.2}s` }} aria-hidden="true" />
                <StageIcon kind={s.kind} />
                <h3>{s.title}</h3>
                <p>{s.text}</p>
                <span className="where">{s.where}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <Reveal as="section" className="container popular">
        <div className="page-head" style={{ alignItems: "center", textAlign: "center" }}>
          <h2 className="chapter-heading">start with a favourite</h2>
          <p>Ready-made lessons, checked and ready to play. No API key needed.</p>
        </div>
        <div className="grid-3">
          {popular.map(({ plan: p, label }) => {
            const algo = algorithmById(catalog, p.structure);
            return (
              <div key={p.id} className={`card lesson-card level-${p.level}`}>
                <div className="lc-head">
                  <span className={`lc-level tag-${p.level}`}>{label}</span>
                  {algo && <Emblem category={algo.category} size={44} />}
                </div>
                <div className="lc-body">
                  <h3>{p.title}</h3>
                  <p>{algo?.summary}</p>
                </div>
                <div className="lc-actions">
                  <button type="button" className="btn btn-primary btn-small" onClick={() => watch(p.id)}>Watch</button>
                  {algo && <Link to={`/library/${algo.id}`}>About {algo.title.toLowerCase()}</Link>}
                </div>
              </div>
            );
          })}
        </div>
      </Reveal>

      <section className="faq" id="faq">
        <h2 className="chapter-heading" style={{ textAlign: "center" }}>questions</h2>
        {FAQ.map(([q, a]) => (
          <details key={q}>
            <summary>{q}</summary>
            <p>{a}</p>
          </details>
        ))}
      </section>

      <section className="green-close">
        <div className="valley">
          <CtaHelper />
          <h2 className="display">ready to see it move?</h2>
          <LinkButton to="/studio" wide>Make a lesson</LinkButton>
        </div>
        <FooterLayers />
      </section>
    </>
  );
}
