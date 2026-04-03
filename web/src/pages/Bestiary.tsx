import { useEffect, useRef, useState } from "react";

interface Creature {
  id: number;
  name: string;
  size: string;
  creature_type: string;
  cr: number;
  hp: number;
  hp_formula: string | null;
  ac: number;
  ac_notes: string | null;
  speed: string;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  source: string | null;
  notes: string | null;
  traits: string | null;
  actions: string | null;
  senses: string | null;
  languages: string | null;
  damage_resistances: string | null;
  damage_immunities: string | null;
  condition_immunities: string | null;
}

const BLANK: Partial<Creature> = {
  name: "",
  size: "Medium",
  creature_type: "humanoid",
  cr: 1,
  hp: 10,
  hp_formula: "",
  ac: 12,
  ac_notes: "",
  speed: "30 ft.",
  strength: 10,
  dexterity: 10,
  constitution: 10,
  intelligence: 10,
  wisdom: 10,
  charisma: 10,
  source: "",
  notes: "",
};

const SIZES = ["Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"];
const TYPES = [
  "aberration", "beast", "celestial", "construct", "dragon", "elemental",
  "fey", "fiend", "giant", "humanoid", "monstrosity", "ooze", "plant", "undead",
];
const CR_OPTIONS = [
  { label: "0", value: 0 },
  { label: "1/8", value: 0.125 },
  { label: "1/4", value: 0.25 },
  { label: "1/2", value: 0.5 },
  ...Array.from({ length: 30 }, (_, i) => ({ label: String(i + 1), value: i + 1 })),
];

function crLabel(cr: number): string {
  const mapping: Record<number, string> = { 0.125: "1/8", 0.25: "1/4", 0.5: "1/2" };
  if (cr in mapping) return mapping[cr];
  return String(Math.round(cr));
}

function modifier(score: number): string {
  const mod = Math.floor((score - 10) / 2);
  return mod >= 0 ? `+${mod}` : String(mod);
}

interface ApiMonster {
  index: string;
  name: string;
}

export default function Bestiary() {
  const [creatures, setCreatures] = useState<Creature[]>([]);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [selected, setSelected] = useState<Creature | null>(null);
  const [editing, setEditing] = useState<Partial<Creature> | null>(null);
  const [isNew, setIsNew] = useState(false);

  // D&D API import state
  const [apiSearch, setApiSearch] = useState("");
  const [apiResults, setApiResults] = useState<ApiMonster[]>([]);
  const [apiLoading, setApiLoading] = useState(false);
  const [importing, setImporting] = useState<string | null>(null);
  const [showImport, setShowImport] = useState(false);
  const apiDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // AI generation state
  const [showAiPanel, setShowAiPanel] = useState(false);
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiCr, setAiCr] = useState<number>(1);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [aiPreview, setAiPreview] = useState<Partial<Creature> | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);

  async function load() {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (typeFilter) params.set("creature_type", typeFilter);
    const r = await fetch(`/api/creatures?${params}`);
    setCreatures(await r.json());
  }

  useEffect(() => {
    load();
  }, [search, typeFilter]);

  async function save() {
    if (!editing) return;
    const method = isNew ? "POST" : "PATCH";
    const url = isNew ? "/api/creatures" : `/api/creatures/${editing.id}`;
    await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(editing),
    });
    setEditing(null);
    setIsNew(false);
    load();
  }

  async function del(id: number) {
    if (!confirm("Delete this creature?")) return;
    await fetch(`/api/creatures/${id}`, { method: "DELETE" });
    if (selected?.id === id) setSelected(null);
    load();
  }

  function startNew() {
    setEditing({ ...BLANK });
    setIsNew(true);
    setSelected(null);
  }

  function startEdit(c: Creature) {
    setEditing({ ...c });
    setIsNew(false);
  }

  function handleApiSearchChange(value: string) {
    setApiSearch(value);
    if (apiDebounceRef.current) clearTimeout(apiDebounceRef.current);
    if (!value.trim()) { setApiResults([]); return; }
    apiDebounceRef.current = setTimeout(async () => {
      setApiLoading(true);
      try {
        const r = await fetch(`/api/dnd/monsters?search=${encodeURIComponent(value)}`);
        setApiResults(await r.json());
      } catch {
        setApiResults([]);
      } finally {
        setApiLoading(false);
      }
    }, 400);
  }

  async function importMonster(index: string) {
    setImporting(index);
    try {
      const r = await fetch(`/api/dnd/monsters/${index}/import`, { method: "POST" });
      if (r.ok) {
        const creature = await r.json();
        load();
        setSelected(creature);
        setShowImport(false);
        setApiSearch("");
        setApiResults([]);
      }
    } finally {
      setImporting(null);
    }
  }

  async function generateWithAi() {
    if (!aiPrompt.trim()) return;
    setAiGenerating(true);
    setAiError(null);
    setAiPreview(null);
    try {
      const r = await fetch("/api/ai/generate-monster", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: aiPrompt, cr: aiCr }),
      });
      if (!r.ok) {
        const body = await r.json();
        setAiError(body.detail ?? "Generation failed");
        return;
      }
      const creature = await r.json();
      setAiPreview(creature);
      setSelected(null);
      setEditing(null);
    } catch {
      setAiError("Network error — is the server running?");
    } finally {
      setAiGenerating(false);
    }
  }

  async function saveAiCreature() {
    if (!aiPreview) return;
    const r = await fetch("/api/creatures", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(aiPreview),
    });
    const saved = await r.json();
    setAiPreview(null);
    setAiPrompt("");
    setShowAiPanel(false);
    load();
    setSelected(saved);
  }

  return (
    <div className="flex gap-4 h-full">
      {/* List panel */}
      <div className="w-72 flex-shrink-0 flex flex-col gap-3">
        <div className="flex gap-2">
          <input
            className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-red-600"
            placeholder="Search creatures..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button
            onClick={startNew}
            className="bg-red-800 hover:bg-red-700 text-white text-sm px-3 py-1.5 rounded"
          >
            + Add
          </button>
        </div>

        {/* D&D API Import */}
        <div className="border border-gray-700 rounded overflow-hidden">
          <button
            onClick={() => setShowImport((v) => !v)}
            className="w-full flex items-center justify-between px-3 py-2 bg-gray-800 hover:bg-gray-750 text-sm text-gray-300"
          >
            <span>📥 Import from SRD</span>
            <span className="text-gray-500">{showImport ? "▲" : "▼"}</span>
          </button>
          {showImport && (
            <div className="p-2 bg-gray-900">
              <input
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-red-600 mb-2"
                placeholder="Search D&D monsters..."
                value={apiSearch}
                onChange={(e) => handleApiSearchChange(e.target.value)}
                autoFocus
              />
              {apiLoading && (
                <div className="text-xs text-gray-500 text-center py-2">Searching...</div>
              )}
              {!apiLoading && apiResults.length === 0 && apiSearch && (
                <div className="text-xs text-gray-500 text-center py-2">No results</div>
              )}
              <div className="max-h-48 overflow-y-auto space-y-0.5 scrollbar-thin">
                {apiResults.map((m) => (
                  <button
                    key={m.index}
                    onClick={() => importMonster(m.index)}
                    disabled={importing === m.index}
                    className="w-full text-left px-2 py-1.5 text-sm rounded hover:bg-gray-700 disabled:opacity-50 flex items-center justify-between"
                  >
                    <span>{m.name}</span>
                    <span className="text-xs text-gray-500">
                      {importing === m.index ? "importing..." : "import"}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
        {/* AI monster generation */}
        <div className="border border-gray-700 rounded overflow-hidden">
          <button
            onClick={() => { setShowAiPanel((v) => !v); setAiPreview(null); setAiError(null); }}
            className="w-full flex items-center justify-between px-3 py-2 bg-gray-800 hover:bg-gray-750 text-sm text-gray-300"
          >
            <span>✨ Generate with AI</span>
            <span className="text-gray-500">{showAiPanel ? "▲" : "▼"}</span>
          </button>
          {showAiPanel && (
            <div className="p-2 bg-gray-900 space-y-2">
              <div>
                <div className="text-xs text-gray-400 mb-1">Challenge Rating</div>
                <select
                  className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-red-600"
                  value={aiCr}
                  onChange={(e) => setAiCr(parseFloat(e.target.value))}
                >
                  {CR_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <textarea
                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-red-600 resize-none h-24"
                placeholder="Describe your monster... e.g. 'An undead pirate captain who commands ghostly crew and wields a cursed cutlass'"
                value={aiPrompt}
                onChange={(e) => setAiPrompt(e.target.value)}
              />
              {aiError && (
                <p className="text-xs text-red-400">{aiError}</p>
              )}
              <button
                onClick={generateWithAi}
                disabled={aiGenerating || !aiPrompt.trim()}
                className="w-full bg-red-800 hover:bg-red-700 disabled:opacity-40 text-white text-sm px-3 py-1.5 rounded font-medium"
              >
                {aiGenerating ? "Generating..." : aiPreview ? "Regenerate" : "Generate Monster"}
              </button>
              {aiPreview && (
                <button
                  onClick={saveAiCreature}
                  className="w-full bg-green-800 hover:bg-green-700 text-white text-sm px-3 py-1.5 rounded font-medium"
                >
                  ✓ Save to Bestiary
                </button>
              )}
            </div>
          )}
        </div>

        <select
          className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">All types</option>
          {TYPES.map((t) => (
            <option key={t} value={t}>
              {t[0].toUpperCase() + t.slice(1)}
            </option>
          ))}
        </select>

        <div className="flex-1 overflow-y-auto space-y-1 scrollbar-thin">
          {creatures.length === 0 && (
            <p className="text-gray-500 text-sm text-center py-8">
              No creatures yet. Add one!
            </p>
          )}
          {creatures.map((c) => (
            <button
              key={c.id}
              onClick={() => { setSelected(c); setEditing(null); }}
              className={`w-full text-left px-3 py-2 rounded border text-sm transition-colors ${
                selected?.id === c.id
                  ? "bg-red-900/40 border-red-700 text-red-200"
                  : "bg-gray-900 border-gray-800 hover:border-gray-600 text-gray-300"
              }`}
            >
              <div className="font-medium">{c.name}</div>
              <div className="text-xs text-gray-500">
                CR {crLabel(c.cr)} · {c.creature_type} · HP {c.hp} · AC {c.ac}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Detail / edit panel */}
      <div className="flex-1 bg-gray-900 border border-gray-800 rounded-lg p-5 overflow-y-auto scrollbar-thin">
        {editing ? (
          <CreatureForm
            data={editing}
            onChange={setEditing}
            onSave={save}
            onCancel={() => { setEditing(null); setIsNew(false); }}
          />
        ) : aiPreview ? (
          <div>
            <div className="flex items-center gap-2 mb-4 bg-red-950/40 border border-red-800 rounded px-3 py-2 text-sm">
              <span className="text-red-400">✨</span>
              <span className="text-red-200 font-medium">AI Preview — not yet saved</span>
              <span className="text-gray-500 ml-auto text-xs">Tweak your prompt and regenerate, or save when ready.</span>
            </div>
            <CreatureDetail
              creature={aiPreview as Creature}
              onEdit={() => { setEditing({ ...aiPreview }); setIsNew(true); setAiPreview(null); }}
              onDelete={() => { setAiPreview(null); }}
              onSave={saveAiCreature}
            />
          </div>
        ) : selected ? (
          <CreatureDetail
            creature={selected}
            onEdit={() => startEdit(selected)}
            onDelete={() => del(selected.id)}
          />
        ) : (
          <div className="text-gray-500 text-center mt-20">
            Select a creature or add a new one
          </div>
        )}
      </div>
    </div>
  );
}

function CreatureDetail({
  creature,
  onEdit,
  onDelete,
  onSave,
}: {
  creature: Creature;
  onEdit: () => void;
  onDelete: () => void;
  onSave?: () => void;
}) {
  const stats: [string, number][] = [
    ["STR", creature.strength],
    ["DEX", creature.dexterity],
    ["CON", creature.constitution],
    ["INT", creature.intelligence],
    ["WIS", creature.wisdom],
    ["CHA", creature.charisma],
  ];

  return (
    <div>
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-red-300">{creature.name}</h2>
          <p className="text-gray-400 text-sm">
            {creature.size} {creature.creature_type}
            {creature.source && ` · ${creature.source}`}
          </p>
        </div>
        <div className="flex gap-2">
          {onSave && (
            <button
              onClick={onSave}
              className="bg-green-800 hover:bg-green-700 text-white text-sm px-3 py-1.5 rounded font-medium"
            >
              ✓ Save to Bestiary
            </button>
          )}
          <button
            onClick={onEdit}
            className="bg-gray-700 hover:bg-gray-600 text-white text-sm px-3 py-1.5 rounded"
          >
            {onSave ? "Edit before saving" : "Edit"}
          </button>
          {!onSave && (
            <button
              onClick={onDelete}
              className="bg-red-900 hover:bg-red-800 text-white text-sm px-3 py-1.5 rounded"
            >
              Delete
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <Stat label="Armor Class" value={`${creature.ac}${creature.ac_notes ? ` (${creature.ac_notes})` : ""}`} />
        <Stat label="Hit Points" value={`${creature.hp}${creature.hp_formula ? ` (${creature.hp_formula})` : ""}`} />
        <Stat label="Speed" value={creature.speed} />
        <Stat label="CR" value={crLabel(creature.cr)} />
      </div>

      {/* Ability scores */}
      <div className="grid grid-cols-6 gap-2 bg-gray-800 rounded p-3 mb-4 text-center">
        {stats.map(([label, score]) => (
          <div key={label}>
            <div className="text-xs text-gray-400 font-medium">{label}</div>
            <div className="text-lg font-bold">{score}</div>
            <div className="text-xs text-gray-400">{modifier(score)}</div>
          </div>
        ))}
      </div>

      {creature.senses && (
        <InfoRow label="Senses" value={creature.senses} />
      )}
      {creature.languages && (
        <InfoRow label="Languages" value={creature.languages} />
      )}
      {creature.damage_resistances && (
        <InfoRow label="Damage Resistances" value={creature.damage_resistances} />
      )}
      {creature.damage_immunities && (
        <InfoRow label="Damage Immunities" value={creature.damage_immunities} />
      )}
      {creature.condition_immunities && (
        <InfoRow label="Condition Immunities" value={creature.condition_immunities} />
      )}

      {creature.traits && renderJsonList("Traits", creature.traits)}
      {creature.actions && renderJsonList("Actions", creature.actions)}

      {creature.notes && (
        <div className="mt-4 bg-gray-800 rounded p-3 text-sm text-gray-300">
          <div className="font-semibold text-gray-200 mb-1">Notes</div>
          {creature.notes}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-800 rounded p-2">
      <div className="text-xs text-gray-400">{label}</div>
      <div className="font-semibold text-sm">{value}</div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-2 text-sm mb-1">
      <span className="font-medium text-gray-300 min-w-36">{label}:</span>
      <span className="text-gray-400">{value}</span>
    </div>
  );
}

function renderJsonList(title: string, json: string) {
  let items: { name: string; description: string }[] = [];
  try {
    items = JSON.parse(json);
  } catch {
    return null;
  }
  if (!Array.isArray(items) || items.length === 0) return null;
  return (
    <div className="mt-3">
      <h3 className="text-red-400 font-semibold border-b border-red-900 pb-1 mb-2">
        {title}
      </h3>
      {items.map((item, i) => (
        <div key={i} className="mb-2 text-sm">
          <span className="font-semibold text-gray-200">{item.name}. </span>
          <span className="text-gray-400">{item.description}</span>
        </div>
      ))}
    </div>
  );
}

function CreatureForm({
  data,
  onChange,
  onSave,
  onCancel,
}: {
  data: Partial<Creature>;
  onChange: (d: Partial<Creature>) => void;
  onSave: () => void;
  onCancel: () => void;
}) {
  function set(key: keyof Creature, value: unknown) {
    onChange({ ...data, [key]: value });
  }

  return (
    <div>
      <h2 className="text-xl font-bold text-red-300 mb-4">
        {data.id ? "Edit Creature" : "New Creature"}
      </h2>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="col-span-2">
          <Label>Name</Label>
          <Input value={data.name ?? ""} onChange={(v) => set("name", v)} />
        </div>
        <div>
          <Label>Size</Label>
          <select
            className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm"
            value={data.size ?? "Medium"}
            onChange={(e) => set("size", e.target.value)}
          >
            {SIZES.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <Label>Type</Label>
          <select
            className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm"
            value={data.creature_type ?? "humanoid"}
            onChange={(e) => set("creature_type", e.target.value)}
          >
            {TYPES.map((t) => <option key={t} value={t}>{t[0].toUpperCase() + t.slice(1)}</option>)}
          </select>
        </div>
        <div>
          <Label>CR</Label>
          <select
            className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm"
            value={data.cr ?? 1}
            onChange={(e) => set("cr", parseFloat(e.target.value))}
          >
            {CR_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
        <div>
          <Label>Speed</Label>
          <Input value={data.speed ?? "30 ft."} onChange={(v) => set("speed", v)} />
        </div>
        <div>
          <Label>HP</Label>
          <NumInput value={data.hp ?? 10} onChange={(v) => set("hp", v)} />
        </div>
        <div>
          <Label>HP Formula (optional)</Label>
          <Input value={data.hp_formula ?? ""} onChange={(v) => set("hp_formula", v)} placeholder="e.g. 4d8+4" />
        </div>
        <div>
          <Label>AC</Label>
          <NumInput value={data.ac ?? 10} onChange={(v) => set("ac", v)} />
        </div>
        <div>
          <Label>AC Notes (optional)</Label>
          <Input value={data.ac_notes ?? ""} onChange={(v) => set("ac_notes", v)} placeholder="e.g. natural armor" />
        </div>
      </div>

      {/* Ability scores */}
      <h3 className="text-gray-400 text-sm font-semibold mb-2">Ability Scores</h3>
      <div className="grid grid-cols-6 gap-2 mb-4">
        {(["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"] as const).map((stat) => (
          <div key={stat} className="text-center">
            <Label>{stat.slice(0, 3).toUpperCase()}</Label>
            <NumInput
              value={(data[stat] as number) ?? 10}
              onChange={(v) => set(stat, v)}
              min={1}
              max={30}
            />
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <Label>Senses</Label>
          <Input value={data.senses ?? ""} onChange={(v) => set("senses", v)} placeholder="darkvision 60 ft., ..." />
        </div>
        <div>
          <Label>Languages</Label>
          <Input value={data.languages ?? ""} onChange={(v) => set("languages", v)} />
        </div>
        <div>
          <Label>Damage Resistances</Label>
          <Input value={data.damage_resistances ?? ""} onChange={(v) => set("damage_resistances", v)} />
        </div>
        <div>
          <Label>Damage Immunities</Label>
          <Input value={data.damage_immunities ?? ""} onChange={(v) => set("damage_immunities", v)} />
        </div>
        <div>
          <Label>Condition Immunities</Label>
          <Input value={data.condition_immunities ?? ""} onChange={(v) => set("condition_immunities", v)} />
        </div>
        <div>
          <Label>Source</Label>
          <Input value={data.source ?? ""} onChange={(v) => set("source", v)} placeholder="Monster Manual, Custom, ..." />
        </div>
      </div>

      <div className="mb-4">
        <Label>Notes</Label>
        <textarea
          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-red-600 h-20 resize-none"
          value={data.notes ?? ""}
          onChange={(e) => set("notes", e.target.value)}
        />
      </div>

      <div className="flex gap-2">
        <button
          onClick={onSave}
          className="bg-red-800 hover:bg-red-700 text-white px-4 py-2 rounded text-sm font-medium"
        >
          Save
        </button>
        <button
          onClick={onCancel}
          className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm font-medium"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return <div className="text-xs text-gray-400 mb-1">{children}</div>;
}

function Input({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <input
      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-red-600"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  );
}

function NumInput({
  value,
  onChange,
  min = 0,
  max = 999,
}: {
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
}) {
  return (
    <input
      type="number"
      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-red-600"
      value={value}
      min={min}
      max={max}
      onChange={(e) => onChange(parseInt(e.target.value) || 0)}
    />
  );
}
