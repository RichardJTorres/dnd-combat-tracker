import { useEffect, useState } from "react";

interface Provider {
  id: string;
  label: string;
  configured: boolean;
}

interface AppSettings {
  provider: string;
  model: string | null;
}

interface ImageSettings {
  provider: string;
  model: string | null;
}

interface Model {
  id: string;
  display_name: string;
}

export default function Settings() {
  const [appSettings, setAppSettings] = useState<AppSettings | null>(null);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [saving, setSaving] = useState(false);
  const [savedMsg, setSavedMsg] = useState("");

  // Image generation state
  const [imageSettings, setImageSettings] = useState<ImageSettings | null>(null);
  const [imageProviders, setImageProviders] = useState<Provider[]>([]);
  const [imageModels, setImageModels] = useState<Model[]>([]);
  const [imageSaving, setImageSaving] = useState(false);
  const [imageSavedMsg, setImageSavedMsg] = useState("");

  async function load() {
    const [settingsRes, providersRes, imageSettingsRes, imageProvidersRes] = await Promise.all([
      fetch("/api/settings").then((r) => r.json()),
      fetch("/api/settings/providers").then((r) => r.json()),
      fetch("/api/settings/image").then((r) => r.json()),
      fetch("/api/settings/image-providers").then((r) => r.json()),
    ]);
    setAppSettings(settingsRes);
    setProviders(providersRes);
    setImageSettings(imageSettingsRes);
    setImageProviders(imageProvidersRes);
    await Promise.all([
      loadModels(settingsRes.provider),
      imageSettingsRes.provider ? loadImageModels(imageSettingsRes.provider) : Promise.resolve(),
    ]);
  }

  async function loadModels(provider: string) {
    setModels([]);
    const r = await fetch(`/api/settings/providers/${provider}/models`);
    if (r.ok) setModels(await r.json());
  }

  async function loadImageModels(provider: string) {
    setImageModels([]);
    const r = await fetch(`/api/settings/image-providers/${provider}/models`);
    if (r.ok) setImageModels(await r.json());
  }

  useEffect(() => { load(); }, []);

  async function setProvider(provider: string) {
    setSaving(true);
    const r = await fetch("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider }),
    });
    const updated = await r.json();
    setAppSettings(updated);
    setSaving(false);
    await loadModels(provider);
  }

  async function setModel(model: string) {
    if (!appSettings) return;
    setSaving(true);
    const r = await fetch("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: appSettings.provider, model }),
    });
    const updated = await r.json();
    setAppSettings(updated);
    setSaving(false);
    setSavedMsg("Saved!");
    setTimeout(() => setSavedMsg(""), 2000);
  }

  async function setImageProvider(provider: string) {
    setImageSaving(true);
    const r = await fetch("/api/settings/image", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider }),
    });
    const updated = await r.json();
    setImageSettings(updated);
    setImageSaving(false);
    if (provider) await loadImageModels(provider);
    else setImageModels([]);
  }

  async function setImageModel(model: string) {
    if (!imageSettings) return;
    setImageSaving(true);
    const r = await fetch("/api/settings/image", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: imageSettings.provider, model }),
    });
    const updated = await r.json();
    setImageSettings(updated);
    setImageSaving(false);
    setImageSavedMsg("Saved!");
    setTimeout(() => setImageSavedMsg(""), 2000);
  }

  if (!appSettings) return <div className="text-ink-400 italic p-8">Loading...</div>;

  return (
    <div className="max-w-xl mx-auto">
      <h2 className="text-xl font-display font-bold text-crimson-600 mb-6">AI Settings</h2>

      {/* ── Image Generation ────────────────────────────────────────────── */}
      <h3 className="text-base font-display font-bold text-crimson-600 mb-3">Image Generation</h3>

      <section className="panel p-5 mb-4">
        <h3 className="text-sm font-display font-semibold text-ink-800 mb-3 uppercase tracking-wide">Image Provider</h3>
        <div className="space-y-2">
          {/* Disabled / none option */}
          <label className={`flex items-center gap-3 p-3 rounded border cursor-pointer transition-colors ${
            !imageSettings?.provider
              ? "bg-crimson-900/20 border-crimson-500"
              : "bg-parchment-200 border-leather-600 hover:border-leather-400"
          }`}>
            <input
              type="radio"
              name="image_provider"
              value=""
              checked={!imageSettings?.provider}
              onChange={() => setImageProvider("")}
              className="accent-crimson-600"
            />
            <span className="flex-1 text-sm text-ink-400 italic">Disabled</span>
          </label>
          {imageProviders.map((p) => (
            <label
              key={p.id}
              className={`flex items-center gap-3 p-3 rounded border cursor-pointer transition-colors ${
                imageSettings?.provider === p.id
                  ? "bg-crimson-900/20 border-crimson-500"
                  : "bg-parchment-200 border-leather-600 hover:border-leather-400"
              }`}
            >
              <input
                type="radio"
                name="image_provider"
                value={p.id}
                checked={imageSettings?.provider === p.id}
                onChange={() => setImageProvider(p.id)}
                className="accent-crimson-600"
              />
              <span className="flex-1 text-sm text-ink-800">{p.label}</span>
              <span className={`text-xs px-2 py-0.5 rounded ${
                p.configured
                  ? "bg-hp-good/80 text-parchment-100"
                  : "bg-parchment-300 text-ink-400 border border-leather-600"
              }`}>
                {p.configured ? "configured" : "unavailable"}
              </span>
            </label>
          ))}
        </div>
        <p className="text-xs text-ink-400 italic mt-3">
          Set <code>GEMINI_API_KEY</code> for Gemini image generation.
          Forge requires a running local server (set <code>FORGE_IMAGE_HOST</code> if not on localhost).
        </p>
      </section>

      {imageSettings?.provider && (
        <section className="panel p-5 mb-4">
          <h3 className="text-sm font-display font-semibold text-ink-800 mb-3 uppercase tracking-wide">Image Model</h3>
          {imageModels.length === 0 ? (
            <p className="text-sm text-ink-400 italic">
              {imageProviders.find((p) => p.id === imageSettings.provider)?.configured
                ? "Loading models..."
                : "Provider unavailable — cannot load models."}
            </p>
          ) : (
            <select
              className="input-fantasy w-full"
              value={imageSettings.model ?? ""}
              onChange={(e) => setImageModel(e.target.value)}
            >
              {imageModels.map((m) => (
                <option key={m.id} value={m.id}>{m.display_name}</option>
              ))}
            </select>
          )}
        </section>
      )}

      <div className="flex items-center gap-3 text-sm mb-6">
        {imageSaving && <span className="text-ink-400 italic">Saving...</span>}
        {imageSavedMsg && <span className="text-hp-good font-semibold">{imageSavedMsg}</span>}
      </div>

      {/* ── LLM Settings ─────────────────────────────────────────────────── */}
      <h3 className="text-base font-display font-bold text-crimson-600 mb-3">Language Model</h3>

      {/* Provider selection */}
      <section className="panel p-5 mb-4">
        <h3 className="text-sm font-display font-semibold text-ink-800 mb-3 uppercase tracking-wide">LLM Provider</h3>
        <div className="space-y-2">
          {providers.map((p) => (
            <label
              key={p.id}
              className={`flex items-center gap-3 p-3 rounded border cursor-pointer transition-colors ${
                appSettings.provider === p.id
                  ? "bg-crimson-900/20 border-crimson-500"
                  : "bg-parchment-200 border-leather-600 hover:border-leather-400"
              }`}
            >
              <input
                type="radio"
                name="provider"
                value={p.id}
                checked={appSettings.provider === p.id}
                onChange={() => setProvider(p.id)}
                className="accent-crimson-600"
              />
              <span className="flex-1 text-sm text-ink-800">{p.label}</span>
              <span
                className={`text-xs px-2 py-0.5 rounded ${
                  p.configured
                    ? "bg-hp-good/80 text-parchment-100"
                    : "bg-parchment-300 text-ink-400 border border-leather-600"
                }`}
              >
                {p.configured ? "configured" : "no key"}
              </span>
            </label>
          ))}
        </div>
        <p className="text-xs text-ink-400 italic mt-3">
          Set API keys via environment variables:{" "}
          <code>ANTHROPIC_API_KEY</code>,{" "}
          <code>GEMINI_API_KEY</code>,{" "}
          <code>OPENAI_API_KEY</code>.
          Ollama requires a running local server.
        </p>
      </section>

      {/* Model selection */}
      <section className="panel p-5 mb-4">
        <h3 className="text-sm font-display font-semibold text-ink-800 mb-3 uppercase tracking-wide">Model</h3>
        {models.length === 0 ? (
          <p className="text-sm text-ink-400 italic">
            {providers.find((p) => p.id === appSettings.provider)?.configured
              ? "Loading models..."
              : "Configure an API key to see available models."}
          </p>
        ) : (
          <select
            className="input-fantasy w-full"
            value={appSettings.model ?? ""}
            onChange={(e) => setModel(e.target.value)}
          >
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.display_name}
              </option>
            ))}
          </select>
        )}
        {appSettings.model && models.length === 0 && (
          <p className="text-xs text-ink-400 mt-2">
            Current: <code>{appSettings.model}</code>
          </p>
        )}
      </section>

      {/* Status */}
      <div className="flex items-center gap-3 text-sm">
        {saving && <span className="text-ink-400 italic">Saving...</span>}
        {savedMsg && <span className="text-hp-good font-semibold">{savedMsg}</span>}
      </div>

      {/* Current config summary */}
      <section className="panel-inset p-4 mt-4 text-xs text-ink-400">
        <div>Active provider: <span className="text-ink-800 font-semibold">{appSettings.provider}</span></div>
        {appSettings.model && (
          <div>Active model: <span className="text-ink-800 font-semibold">{appSettings.model}</span></div>
        )}
      </section>
    </div>
  );
}
