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

  if (!appSettings) return <div className="text-gray-500 p-8">Loading...</div>;

  return (
    <div className="max-w-xl mx-auto">
      <h2 className="text-xl font-bold text-red-300 mb-6">AI Settings</h2>

      {/* ── Image Generation ────────────────────────────────────────────── */}
      <h3 className="text-base font-semibold text-gray-300 mb-3">Image Generation</h3>

      <section className="bg-gray-900 border border-gray-800 rounded-lg p-5 mb-4">
        <h4 className="text-sm font-semibold text-gray-300 mb-3">Image Provider</h4>
        <div className="space-y-2">
          {/* Disabled / none option */}
          <label className={`flex items-center gap-3 p-3 rounded border cursor-pointer transition-colors ${
            !imageSettings?.provider
              ? "bg-red-900/30 border-red-700"
              : "bg-gray-800 border-gray-700 hover:border-gray-600"
          }`}>
            <input
              type="radio"
              name="image_provider"
              value=""
              checked={!imageSettings?.provider}
              onChange={() => setImageProvider("")}
              className="accent-red-500"
            />
            <span className="flex-1 text-sm text-gray-400">Disabled</span>
          </label>
          {imageProviders.map((p) => (
            <label
              key={p.id}
              className={`flex items-center gap-3 p-3 rounded border cursor-pointer transition-colors ${
                imageSettings?.provider === p.id
                  ? "bg-red-900/30 border-red-700"
                  : "bg-gray-800 border-gray-700 hover:border-gray-600"
              }`}
            >
              <input
                type="radio"
                name="image_provider"
                value={p.id}
                checked={imageSettings?.provider === p.id}
                onChange={() => setImageProvider(p.id)}
                className="accent-red-500"
              />
              <span className="flex-1 text-sm">{p.label}</span>
              <span className={`text-xs px-2 py-0.5 rounded ${
                p.configured ? "bg-green-900 text-green-300" : "bg-gray-700 text-gray-500"
              }`}>
                {p.configured ? "configured" : "unavailable"}
              </span>
            </label>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-3">
          Set <code className="text-gray-400">GEMINI_API_KEY</code> for Gemini image generation.
          Forge requires a running local server (set <code className="text-gray-400">FORGE_IMAGE_HOST</code> if not on localhost).
        </p>
      </section>

      {imageSettings?.provider && (
        <section className="bg-gray-900 border border-gray-800 rounded-lg p-5 mb-4">
          <h4 className="text-sm font-semibold text-gray-300 mb-3">Image Model</h4>
          {imageModels.length === 0 ? (
            <p className="text-sm text-gray-500">
              {imageProviders.find((p) => p.id === imageSettings.provider)?.configured
                ? "Loading models..."
                : "Provider unavailable — cannot load models."}
            </p>
          ) : (
            <select
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-red-600"
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
        {imageSaving && <span className="text-gray-400">Saving...</span>}
        {imageSavedMsg && <span className="text-green-400">{imageSavedMsg}</span>}
      </div>

      {/* ── LLM Settings ─────────────────────────────────────────────────── */}
      <h3 className="text-base font-semibold text-gray-300 mb-3">Language Model</h3>

      {/* Provider selection */}
      <section className="bg-gray-900 border border-gray-800 rounded-lg p-5 mb-4">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">LLM Provider</h3>
        <div className="space-y-2">
          {providers.map((p) => (
            <label
              key={p.id}
              className={`flex items-center gap-3 p-3 rounded border cursor-pointer transition-colors ${
                appSettings.provider === p.id
                  ? "bg-red-900/30 border-red-700"
                  : "bg-gray-800 border-gray-700 hover:border-gray-600"
              }`}
            >
              <input
                type="radio"
                name="provider"
                value={p.id}
                checked={appSettings.provider === p.id}
                onChange={() => setProvider(p.id)}
                className="accent-red-500"
              />
              <span className="flex-1 text-sm">{p.label}</span>
              <span
                className={`text-xs px-2 py-0.5 rounded ${
                  p.configured
                    ? "bg-green-900 text-green-300"
                    : "bg-gray-700 text-gray-500"
                }`}
              >
                {p.configured ? "configured" : "no key"}
              </span>
            </label>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-3">
          Set API keys via environment variables:{" "}
          <code className="text-gray-400">ANTHROPIC_API_KEY</code>,{" "}
          <code className="text-gray-400">GEMINI_API_KEY</code>,{" "}
          <code className="text-gray-400">OPENAI_API_KEY</code>.
          Ollama requires a running local server.
        </p>
      </section>

      {/* Model selection */}
      <section className="bg-gray-900 border border-gray-800 rounded-lg p-5 mb-4">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Model</h3>
        {models.length === 0 ? (
          <p className="text-sm text-gray-500">
            {providers.find((p) => p.id === appSettings.provider)?.configured
              ? "Loading models..."
              : "Configure an API key to see available models."}
          </p>
        ) : (
          <select
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-red-600"
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
          <p className="text-xs text-gray-400 mt-2">
            Current: <code>{appSettings.model}</code>
          </p>
        )}
      </section>

      {/* Status */}
      <div className="flex items-center gap-3 text-sm">
        {saving && <span className="text-gray-400">Saving...</span>}
        {savedMsg && <span className="text-green-400">{savedMsg}</span>}
      </div>

      {/* Current config summary */}
      <section className="bg-gray-900 border border-gray-800 rounded-lg p-4 mt-4 text-xs text-gray-500">
        <div>Active provider: <span className="text-gray-300">{appSettings.provider}</span></div>
        {appSettings.model && (
          <div>Active model: <span className="text-gray-300">{appSettings.model}</span></div>
        )}
      </section>
    </div>
  );
}
