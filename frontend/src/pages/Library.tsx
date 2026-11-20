import { useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { algorithmById, api, LEVELS, type Level, presetTopic, useCatalog, useHealth, usePlans } from "../api";
import { BenefitArt, Emblem } from "../components/art";
import { Button, ErrorNotice, LevelTag, Loading, Notice, Segmented, Tag } from "../components/ui";

export function LibraryPage() {
  const { data: catalog, isLoading } = useCatalog();
  const { data: plans } = usePlans();
  const [params, setParams] = useSearchParams();
  const category = params.get("category") ?? "all";
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState<Level | "any">("any");
  if (isLoading || !catalog) return <Loading what="Loading the library" />;
  const count = (id: string) => plans?.filter((p) => algorithmById(catalog, p.structure)?.id === id).length ?? 0;
  const matches = catalog.algorithms.filter((a) =>
    (category === "all" || a.category === category) && (level === "any" || a.difficulty === level) &&
    `${a.title} ${a.summary} ${a.category_title}`.toLowerCase().includes(query.toLowerCase()));
  const groups = Object.entries(catalog.categories)
    .map(([id, title]) => ({ id, title, items: matches.filter((a) => a.category === id) }))
    .filter((g) => g.items.length);
  return (
    <div className="container page" style={{ maxWidth: 1200 }}>
      <div className="page-head">
        <h1 className="page-title">Library</h1>
        <p>{catalog.algorithms.length} data structures and algorithms, each with a simulator the verifier trusts and a
          ready-made lesson you can watch without an API key.</p>
      </div>
      <div className="toolbar">
        <input className="input" type="search" placeholder="Search algorithms" value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Search algorithms" />
        <div className="chips" aria-label="Category">
          <button type="button" className="chip" aria-pressed={category === "all"} onClick={() => setParams({})}>All</button>
          {Object.entries(catalog.categories).map(([id, title]) => (
            <button key={id} type="button" className="chip" aria-pressed={category === id} onClick={() => setParams({ category: id })}>
              <Emblem category={id} size={26} />{title}
            </button>
          ))}
        </div>
        <Segmented<Level | "any"> label="Difficulty" options={["any", ...LEVELS]} value={level} onChange={setLevel} />
      </div>
      {groups.length === 0 && <div className="empty">Nothing matches. Try another word, or <Link to="/studio">ask the Studio</Link>.</div>}
      {groups.map((g) => (
        <section key={g.id} className="category-group">
          <h2 className="section-title"><Emblem category={g.id} size={40} />{g.title}</h2>
          <div className="algo-grid">
            {g.items.map((a) => (
              <Link key={a.id} to={`/library/${a.id}`} className="card algo-card">
                <div className="top"><Emblem category={a.category} /><h3>{a.title}</h3></div>
                <p className="small">{a.summary}</p>
                <div className="meta">
                  <LevelTag level={a.difficulty} />
                  <Tag mono>{a.complexity.average}</Tag>
                  <Tag>{count(a.id)} saved lesson{count(a.id) === 1 ? "" : "s"}</Tag>
                </div>
              </Link>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

export function AlgorithmPage() {
  const { algorithmId } = useParams();
  const navigate = useNavigate();
  const { data: catalog, isLoading } = useCatalog();
  const { data: plans } = usePlans();
  const { data: health } = useHealth();
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [op, setOp] = useState<string | null>(null); // the operation whose pseudocode lines are lit
  const algo = algorithmById(catalog, algorithmId);
  if (isLoading) return <Loading />;
  if (!algo) return <div className="container page"><Notice tone="red"><span>No algorithm called “{algorithmId}”. <Link to="/library">Back to the library</Link></span></Notice></div>;
  const saved = plans?.filter((p) => algorithmById(catalog, p.structure)?.id === algo.id) ?? [];

  async function watch(planId: string) {
    setBusy(planId);
    setError(null);
    try {
      const job = await api.renderPlan(planId);
      navigate(`/studio/job/${job.id}`);
    } catch (e) {
      setError(e);
      setBusy(null);
    }
  }
  const studio = (topic: string) => navigate(`/studio?topic=${encodeURIComponent(topic)}&level=${algo.difficulty}`);

  return (
    <div className="container page" style={{ maxWidth: 1100 }}>
      <p style={{ marginBottom: 20 }}><Link to={`/library?category=${algo.category}`}>← {algo.category_title}</Link></p>
      <div className="algo-head">
        <div className="page-head" style={{ marginBottom: 0 }}>
          <div className="actions-row">
            <LevelTag level={algo.difficulty} />
            <Tag>{algo.category_title}</Tag>
            {algo.requires && <Tag>needs {algo.requires}</Tag>}
          </div>
          <h1 className="page-title">{algo.title}</h1>
          <p className="lead">{algo.description}</p>
        </div>
        <div className="art"><BenefitArt kind="library" /></div>
      </div>
      <ErrorNotice error={error} />
      <div className="algo-sections" style={{ marginTop: 40 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 40 }}>
          <section>
            <h2 className="section-title">Saved lessons</h2>
            <p className="small" style={{ margin: "8px 0 4px" }}>Checked by the verifier and ready to play. No API key needed.</p>
            {saved.length === 0 && <p>No saved lesson yet.</p>}
            {saved.map((p) => (
              <div key={p.id} className="plan-row">
                <div className="info">
                  <h3>{p.title}</h3>
                  <div className="actions-row"><LevelTag level={p.level} /><span className="small">{p.steps} steps · {p.questions} quiz questions</span></div>
                </div>
                <Button small onClick={() => watch(p.id)} disabled={busy !== null}>{busy === p.id ? "Starting…" : "Watch"}</Button>
              </div>
            ))}
          </section>
          <section>
            <h2 className="section-title">Make your own</h2>
            <p className="small" style={{ margin: "8px 0 16px" }}>
              Start from a ready-made example, then change the data in the Studio.
              {!health?.llm.configured && <> Making new lessons needs a <Link to="/settings#language-model">language-model key</Link>.</>}
            </p>
            <div className="chips">
              {Object.entries(algo.presets).map(([name, data]) => (
                <button key={name} type="button" className="chip" title={JSON.stringify(data)} onClick={() => studio(presetTopic(algo, name, data))}>
                  {name}
                </button>
              ))}
            </div>
          </section>
          <section>
            <h2 className="section-title">How it works</h2>
            <p className="small" style={{ margin: "8px 0 0" }}>
              The video highlights the lines each step runs. Pick an operation to see which.
            </p>
            <pre className="code" style={{ marginTop: 16 }} aria-label="Pseudocode">
              {algo.pseudocode.map((line, i) => (
                <span key={i} className={op && algo.op_lines[op]?.includes(i) ? "lit" : undefined}>{line}</span>
              ))}
            </pre>
          </section>
        </div>
        <aside style={{ display: "flex", flexDirection: "column", gap: 32 }}>
          <section>
            <h2 className="section-title" style={{ fontSize: 22 }}>Complexity</h2>
            <table className="complexity"><tbody>
              <tr><th>Best time</th><td>{algo.complexity.best}</td></tr>
              <tr><th>Average time</th><td>{algo.complexity.average}</td></tr>
              <tr><th>Worst time</th><td>{algo.complexity.worst}</td></tr>
              <tr><th>Extra space</th><td>{algo.complexity.space}</td></tr>
            </tbody></table>
          </section>
          <section>
            <h2 className="section-title" style={{ fontSize: 22 }}>What the verifier runs</h2>
            <p className="small" style={{ margin: "8px 0 12px" }}>Operations a lesson may use:</p>
            <ul className="ops">
              {Object.entries(algo.operations).map(([name, args]) => (
                <li key={name}>
                  <button type="button" aria-pressed={op === name} onClick={() => setOp(op === name ? null : name)}
                    title="Highlight the pseudocode lines it runs">
                    {name}({args.join(", ")})
                  </button>
                </li>
              ))}
            </ul>
            <p className="small" style={{ margin: "16px 0 12px" }}>Facts it checks in the narration and the quiz:</p>
            <ul className="ops">{algo.facts.map((f) => <li key={f} className={algo.strip.includes(f) ? "shown" : undefined}>{f}</li>)}</ul>
            <p className="small" style={{ margin: "12px 0 0" }}>
              <span className="swatch" aria-hidden="true" /> shown beside the picture after every step
            </p>
          </section>
        </aside>
      </div>
    </div>
  );
}
