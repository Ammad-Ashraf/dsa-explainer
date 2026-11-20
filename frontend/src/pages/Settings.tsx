import { useEffect, useState } from "react";
import { api, type Provider, type Quality, useInvalidate, useProviders, useSettings } from "../api";
import { Button, ErrorNotice, Loading, Notice, Segmented } from "../components/ui";

type TestResult = Awaited<ReturnType<typeof api.testProvider>>;

function ProviderEditor({ provider, active }: { provider: Provider; active: boolean }) {
  const invalidate = useInvalidate();
  const [key, setKey] = useState("");
  const [model, setModel] = useState(provider.saved.model || provider.default_model);
  const [fallback, setFallback] = useState(provider.saved.fallback_model || provider.fallback_model);
  const [baseUrl, setBaseUrl] = useState(provider.saved.base_url);
  const [models, setModels] = useState<string[]>([]);
  const [test, setTest] = useState<TestResult | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    setKey(""); setTest(null); setError(null); setModels([]);
    setModel(provider.saved.model || provider.default_model);
    setFallback(provider.saved.fallback_model || provider.fallback_model);
    setBaseUrl(provider.saved.base_url);
  }, [provider.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const body = () => ({ ...(key ? { api_key: key } : {}), model, fallback_model: fallback, ...(baseUrl ? { base_url: baseUrl } : {}) });
  async function run(name: string, task: () => Promise<unknown>) {
    setBusy(name); setError(null);
    try { await task(); } catch (e) { setError(e); } finally { setBusy(null); }
  }
  const save = (activate: boolean) => run(activate ? "use" : "save", async () => {
    await api.saveProvider(provider.id, { ...body(), activate });
    setKey("");
    invalidate("providers", "health");
  });
  const removeKey = () => run("remove", async () => { await api.saveProvider(provider.id, { api_key: "" }); invalidate("providers", "health"); });
  const runTest = () => run("test", async () => setTest(await api.testProvider(provider.id, { ...(key ? { api_key: key } : {}), model, ...(baseUrl ? { base_url: baseUrl } : {}) })));
  const loadModels = () => run("models", async () => {
    if (key) await api.saveProvider(provider.id, { api_key: key });
    setModels((await api.models(provider.id)).models);
    invalidate("providers");
  });

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div className="row" style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <h3 className="section-title" style={{ fontSize: 22 }}>{provider.name}</h3>
        {provider.key_url && <a href={provider.key_url} target="_blank" rel="noreferrer">{provider.local ? "Download" : "Get a key"} ↗</a>}
      </div>
      {provider.notes && <p className="small">{provider.notes}</p>}
      <div className="form-grid">
        {provider.needs_key && (
          <div className="field">
            <label htmlFor="key">API key</label>
            <input id="key" className="input" type="password" autoComplete="off" value={key} onChange={(e) => setKey(e.target.value)}
              placeholder={provider.saved.key_set ? `Saved (${provider.saved.key_hint}). Type to replace` : "Paste your key"} />
            <span className="hint">Stored only on this computer, and sent only to {provider.name}.</span>
          </div>
        )}
        <div className="field">
          <label htmlFor="model">Model</label>
          <input id="model" className="input" list="model-list" value={model} onChange={(e) => setModel(e.target.value)} placeholder="Pick or type a model" />
          <datalist id="model-list">{models.map((m) => <option key={m} value={m} />)}</datalist>
          <span className="hint"><button type="button" className="btn btn-ghost" style={{ padding: 0 }} onClick={loadModels} disabled={busy !== null}>
            {busy === "models" ? "Loading…" : models.length ? `${models.length} models loaded` : "Load the models this key can use"}</button></span>
        </div>
        <div className="field">
          <label htmlFor="fallback">Fallback model <span className="small">(optional)</span></label>
          <input id="fallback" className="input" value={fallback} onChange={(e) => setFallback(e.target.value)} placeholder="Used when the daily allowance runs out" />
        </div>
        <div className="field">
          <label htmlFor="base">Address</label>
          <input id="base" className="input" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} placeholder={provider.base_url || "https://…/v1"} />
          <span className="hint">{provider.base_url ? "Leave empty for the usual address." : "The server's OpenAI-compatible address."}</span>
        </div>
      </div>
      {test && (test.ok
        ? <Notice tone="green"><span><b>Connected.</b> {test.model} answered in {test.seconds?.toFixed(1)} s.</span></Notice>
        : <Notice tone="red"><span><b>That did not work.</b> {test.error}</span></Notice>)}
      <ErrorNotice error={error} />
      <div className="actions-row">
        <Button onClick={() => save(true)} disabled={busy !== null}>{busy === "use" ? "Saving…" : active ? "Save" : "Save and use"}</Button>
        <Button variant="secondary" onClick={runTest} disabled={busy !== null}>{busy === "test" ? "Testing…" : "Test connection"}</Button>
        {provider.saved.key_set && <Button variant="danger" small onClick={removeKey} disabled={busy !== null}>Remove key</Button>}
      </div>
    </div>
  );
}

function LanguageModel() {
  const { data, isLoading, error } = useProviders();
  const invalidate = useInvalidate();
  const [selected, setSelected] = useState<string | null>(null);
  if (isLoading || !data) return <Loading />;
  const current = selected ?? (data.active && data.active !== "env" ? data.active : data.providers[0].id);
  const provider = data.providers.find((p) => p.id === current)!;
  return (
    <>
      <ErrorNotice error={error} />
      <Notice tone={data.in_use.configured ? "green" : "blue"}>
        <span>{data.in_use.configured
          ? <>In use: <b>{data.in_use.provider_name}</b>, model <b>{data.in_use.model}</b>{data.in_use.local ? " (on this computer)" : ""}.</>
          : <>No language model yet. Saved lessons play without one; to make your own, choose a provider and add a key.</>}</span>
      </Notice>
      {data.env && (
        <div className="actions-row">
          <span className="small">A key is also set in the .env file ({data.env.model}, key {data.env.key_hint}).</span>
          {data.active !== "env" && <Button small variant="secondary" onClick={async () => { await api.activateProvider("env"); invalidate("providers", "health"); }}>Use .env instead</Button>}
        </div>
      )}
      <div className="provider-list">
        {data.providers.map((p) => (
          <button key={p.id} type="button" className="provider-card" aria-pressed={p.id === current} onClick={() => setSelected(p.id)}>
            <b>{p.name}</b>
            <span className={`state${p.ready ? " ok" : ""}`}>{data.active === p.id ? "In use" : p.ready ? "Ready" : p.needs_key ? "Needs a key" : "Needs a model"}</span>
          </button>
        ))}
      </div>
      <ProviderEditor provider={provider} active={data.active === provider.id} />
    </>
  );
}

function Preferences() {
  const { data } = useSettings();
  const invalidate = useInvalidate();
  const [voice, setVoice] = useState("");
  const [saved, setSaved] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);
  useEffect(() => { if (data) setVoice(data.preferences.voice); }, [data?.preferences.voice]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!data) return <Loading />;
  async function save(change: Parameters<typeof api.saveSettings>[0], what: string) {
    setError(null);
    try { await api.saveSettings(change); invalidate("settings", "health"); setSaved(what); } catch (e) { setError(e); }
  }
  return (
    <>
      <section id="voice">
        <h2 className="section-title">Voice</h2>
        <p>The narration is spoken by Kokoro, a voice model that runs on this computer.</p>
        <div className="field" style={{ maxWidth: 420 }}>
          <label htmlFor="voice-name">Voice</label>
          <div className="actions-row">
            <input id="voice-name" className="input" style={{ flex: 1 }} value={voice} onChange={(e) => setVoice(e.target.value)} />
            <Button small variant="secondary" onClick={() => save({ voice }, "voice")}>Save</Button>
          </div>
          <span className="hint">For example af_heart, af_bella, am_michael, bf_emma or bm_george.</span>
        </div>
      </section>
      <section id="video">
        <h2 className="section-title">Video</h2>
        <div className="field">
          <span className="label">Default quality</span>
          <Segmented<Quality> label="Default quality" options={data.qualities} value={data.preferences.default_quality}
            onChange={(q) => save({ default_quality: q }, "quality")} labels={{ draft: "Draft 480p", standard: "720p", high: "1080p" }} />
          <span className="hint">Draft is quickest; 1080p takes about four times as long to draw.</span>
        </div>
        <div className="field" style={{ maxWidth: 420 }}>
          <label htmlFor="workers">Drawing processes</label>
          <input id="workers" className="input" type="number" min={1} max={16} defaultValue={data.preferences.render_workers}
            onBlur={(e) => save({ render_workers: Number(e.target.value) }, "drawing processes")} />
          <span className="hint">How many scenes are drawn at the same time. More is faster, up to the number of CPU cores.</span>
        </div>
        {saved && <Notice tone="green"><span>Saved the {saved}.</span></Notice>}
        <ErrorNotice error={error} />
      </section>
    </>
  );
}

export default function SettingsPage() {
  return (
    <div className="container page" style={{ maxWidth: 1100 }}>
      <div className="page-head"><h1 className="page-title">Settings</h1>
        <p>Everything here is saved on this computer, in settings.json in the app's data folder.</p></div>
      <div className="settings">
        <nav aria-label="Settings sections">
          <a href="#language-model">Language model</a><a href="#voice">Voice</a><a href="#video">Video</a>
        </nav>
        <div>
          <section id="language-model">
            <h2 className="section-title">Language model</h2>
            <p>The planner and the quiz writer use a language model you choose, with your own key. Everything else runs here.</p>
            <LanguageModel />
          </section>
          <Preferences />
        </div>
      </div>
    </div>
  );
}
