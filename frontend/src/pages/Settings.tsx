import { useEffect, useRef, useState } from "react";
import {
  api, type Preferences as Prefs, type Provider, type Quality, useInvalidate, useProviders, useSettings, useVoices, type VoiceInfo,
} from "../api";
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

/** Engine, voice and speed, with a spoken preview. Nothing is saved until "Save voice". */
function VoiceSettings({ prefs, onSave }: { prefs: Prefs; onSave: (change: Partial<Prefs>, what: string) => Promise<void> }) {
  const { data, error: loadError } = useVoices();
  const [engineId, setEngineId] = useState(prefs.voice_engine);
  const [voice, setVoice] = useState(prefs.voice);
  const [speed, setSpeed] = useState(prefs.voice_speed);
  const [preview, setPreview] = useState<{ url: string; key: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const audio = useRef<HTMLAudioElement>(null);
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview.url); }, [preview]);
  if (loadError) return <ErrorNotice error={loadError} />;
  if (!data) return <Loading />;
  const engine = data.engines.find((e) => e.id === engineId) ?? data.engines[0];
  const groups = new Map<string, VoiceInfo[]>();
  for (const v of engine?.voices ?? []) {
    const group = `${v.language === "en-GB" ? "British" : "American"} English · ${v.gender || "voice"}`;
    groups.set(group, [...(groups.get(group) ?? []), v]);
  }
  const changed = engine?.id !== prefs.voice_engine || voice !== prefs.voice || speed !== prefs.voice_speed;
  const key = `${engine?.id}|${voice}|${speed}`;

  async function listen() {
    if (!engine) return;
    if (preview?.key === key) { void audio.current?.play(); return; }
    setBusy(true);
    setError(null);
    try {
      const blob = await api.previewVoice({ engine: engine.id, voice, speed });
      setPreview({ url: URL.createObjectURL(blob), key });
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <p>
        The narration is spoken on this computer by {engine ? <b>{engine.title}</b> : "a local voice model"}; nothing
        is sent anywhere. {engine && <span className="small">Licence: {engine.licence}.</span>}
      </p>
      {engine && !engine.ready && <Notice tone="blue"><span>{engine.title} is not installed yet. {engine.setup}</span></Notice>}
      <div className="voice-grid">
        {data.engines.length > 1 && (
          <div className="field">
            <label htmlFor="voice-engine">Engine</label>
            <select id="voice-engine" className="select" value={engine?.id} onChange={(e) => { setEngineId(e.target.value); setVoice(""); }}>
              {data.engines.map((e) => <option key={e.id} value={e.id}>{e.title}{e.ready ? "" : " (not installed)"}</option>)}
            </select>
          </div>
        )}
        <div className="field">
          <label htmlFor="voice-name">Voice</label>
          <select id="voice-name" className="select" value={voice} onChange={(e) => setVoice(e.target.value)} disabled={!engine?.voices.length}>
            {!engine?.voices.some((v) => v.id === voice) && <option value={voice}>{voice || "Choose a voice"}</option>}
            {[...groups].map(([group, list]) => (
              <optgroup key={group} label={group}>
                {list.map((v) => <option key={v.id} value={v.id}>{v.name.replace(/ \(.*\)$/, "")}</option>)}
              </optgroup>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="voice-speed">Speed <span className="small">{speed.toFixed(2)}×</span></label>
          <input id="voice-speed" type="range" min={0.7} max={1.3} step={0.05} value={speed}
            onChange={(e) => setSpeed(Number(e.target.value))} />
          <span className="hint">Applies to every scene; a revision can still slow one scene down.</span>
        </div>
      </div>
      <div className="actions-row" style={{ marginTop: 16 }}>
        <Button small variant="secondary" onClick={listen} disabled={busy || !engine?.ready || !voice}>
          {busy ? "Speaking…" : preview?.key === key ? "Play again" : "Preview voice"}
        </Button>
        <Button small onClick={() => onSave({ voice_engine: engine!.id, voice, voice_speed: speed }, "voice")} disabled={!changed || !voice}>
          Save voice
        </Button>
      </div>
      {preview && <audio ref={audio} src={preview.url} autoPlay controls style={{ marginTop: 12, width: "100%", maxWidth: 420 }} />}
      {busy && <p className="small" style={{ marginTop: 8 }}>The first preview of a voice takes a few seconds while the model loads.</p>}
      <ErrorNotice error={error} />
    </>
  );
}

function Preferences() {
  const { data } = useSettings();
  const invalidate = useInvalidate();
  const [saved, setSaved] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);
  if (!data) return <Loading />;
  async function save(change: Partial<Prefs>, what: string) {
    setError(null);
    try { await api.saveSettings(change); invalidate("settings", "health", "voices"); setSaved(what); } catch (e) { setError(e); }
  }
  return (
    <>
      <section id="voice">
        <h2 className="section-title">Voice</h2>
        <VoiceSettings key={`${data.preferences.voice_engine}|${data.preferences.voice}|${data.preferences.voice_speed}`}
          prefs={data.preferences} onSave={save} />
        {saved === "voice" && <Notice tone="green"><span>Saved the voice. New scenes use it; existing videos keep theirs.</span></Notice>}
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
        {saved && saved !== "voice" && <Notice tone="green"><span>Saved the {saved}.</span></Notice>}
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
