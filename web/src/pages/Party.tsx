import { useEffect, useState } from "react";

interface Character {
  id: number;
  name: string;
  player_name: string | null;
  character_class: string;
  subclass: string | null;
  level: number;
  race: string | null;
  max_hp: number;
  current_hp: number;
  temp_hp: number;
  ac: number;
  initiative_bonus: number;
  speed: number;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  passive_perception: number;
  notes: string | null;
}

const BLANK: Partial<Character> = {
  name: "",
  player_name: "",
  character_class: "Fighter",
  level: 1,
  race: "",
  max_hp: 10,
  current_hp: 10,
  temp_hp: 0,
  ac: 10,
  initiative_bonus: 0,
  speed: 30,
  strength: 10,
  dexterity: 10,
  constitution: 10,
  intelligence: 10,
  wisdom: 10,
  charisma: 10,
  passive_perception: 10,
  notes: "",
};

const CLASSES = [
  "Artificer", "Barbarian", "Bard", "Cleric", "Druid", "Fighter",
  "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard",
];

function modifier(score: number): string {
  const mod = Math.floor((score - 10) / 2);
  return mod >= 0 ? `+${mod}` : String(mod);
}

function hpColor(current: number, max: number): string {
  const pct = max > 0 ? current / max : 0;
  if (pct <= 0) return "text-gray-500";
  if (pct < 0.25) return "text-red-400";
  if (pct < 0.5) return "text-orange-400";
  if (pct < 0.75) return "text-yellow-400";
  return "text-green-400";
}

export default function Party() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selected, setSelected] = useState<Character | null>(null);
  const [editing, setEditing] = useState<Partial<Character> | null>(null);
  const [isNew, setIsNew] = useState(false);

  async function load() {
    const r = await fetch("/api/characters");
    setCharacters(await r.json());
  }

  useEffect(() => { load(); }, []);

  async function save() {
    if (!editing) return;
    const method = isNew ? "POST" : "PATCH";
    const url = isNew ? "/api/characters" : `/api/characters/${editing.id}`;
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
    if (!confirm("Remove this character from the party?")) return;
    await fetch(`/api/characters/${id}`, { method: "DELETE" });
    if (selected?.id === id) setSelected(null);
    load();
  }

  function startNew() {
    setEditing({ ...BLANK });
    setIsNew(true);
    setSelected(null);
  }

  return (
    <div className="flex gap-4">
      {/* Character list */}
      <div className="w-64 flex-shrink-0 flex flex-col gap-3">
        <button
          onClick={startNew}
          className="w-full bg-red-800 hover:bg-red-700 text-white text-sm px-3 py-2 rounded font-medium"
        >
          + Add Character
        </button>
        <div className="space-y-2">
          {characters.length === 0 && (
            <p className="text-gray-500 text-sm text-center py-8">
              No characters yet
            </p>
          )}
          {characters.map((c) => (
            <button
              key={c.id}
              onClick={() => { setSelected(c); setEditing(null); }}
              className={`w-full text-left px-3 py-3 rounded border transition-colors ${
                selected?.id === c.id
                  ? "bg-red-900/40 border-red-700"
                  : "bg-gray-900 border-gray-800 hover:border-gray-600"
              }`}
            >
              <div className="font-medium text-sm">{c.name}</div>
              <div className="text-xs text-gray-400">
                Level {c.level} {c.character_class}
                {c.player_name && ` · ${c.player_name}`}
              </div>
              <div className={`text-xs font-medium mt-0.5 ${hpColor(c.current_hp, c.max_hp)}`}>
                HP {c.current_hp}/{c.max_hp} · AC {c.ac}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Detail / edit panel */}
      <div className="flex-1 bg-gray-900 border border-gray-800 rounded-lg p-5">
        {editing ? (
          <CharacterForm
            data={editing}
            onChange={setEditing}
            onSave={save}
            onCancel={() => { setEditing(null); setIsNew(false); }}
          />
        ) : selected ? (
          <CharacterDetail
            character={selected}
            onEdit={() => setEditing({ ...selected })}
            onDelete={() => del(selected.id)}
          />
        ) : (
          <div className="text-gray-500 text-center mt-20">
            Select a character or add a new one
          </div>
        )}
      </div>
    </div>
  );
}

function CharacterDetail({
  character: c,
  onEdit,
  onDelete,
}: {
  character: Character;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const stats: [string, number][] = [
    ["STR", c.strength],
    ["DEX", c.dexterity],
    ["CON", c.constitution],
    ["INT", c.intelligence],
    ["WIS", c.wisdom],
    ["CHA", c.charisma],
  ];

  return (
    <div>
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-red-300">{c.name}</h2>
          <p className="text-gray-400 text-sm">
            {c.race ? `${c.race} ` : ""}Level {c.level} {c.character_class}
            {c.subclass ? ` (${c.subclass})` : ""}
            {c.player_name && ` · Played by ${c.player_name}`}
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={onEdit} className="bg-gray-700 hover:bg-gray-600 text-white text-sm px-3 py-1.5 rounded">Edit</button>
          <button onClick={onDelete} className="bg-red-900 hover:bg-red-800 text-white text-sm px-3 py-1.5 rounded">Remove</button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-4">
        <StatBox label="HP" value={`${c.current_hp} / ${c.max_hp}${c.temp_hp > 0 ? ` (+${c.temp_hp})` : ""}`} />
        <StatBox label="AC" value={String(c.ac)} />
        <StatBox label="Initiative" value={`${c.initiative_bonus >= 0 ? "+" : ""}${c.initiative_bonus}`} />
        <StatBox label="Speed" value={`${c.speed} ft.`} />
        <StatBox label="Passive Perception" value={String(c.passive_perception)} />
      </div>

      <div className="grid grid-cols-6 gap-2 bg-gray-800 rounded p-3 mb-4 text-center">
        {stats.map(([label, score]) => (
          <div key={label}>
            <div className="text-xs text-gray-400 font-medium">{label}</div>
            <div className="text-lg font-bold">{score}</div>
            <div className="text-xs text-gray-400">{modifier(score)}</div>
          </div>
        ))}
      </div>

      {c.notes && (
        <div className="bg-gray-800 rounded p-3 text-sm text-gray-300">
          <div className="font-semibold text-gray-200 mb-1">Notes</div>
          {c.notes}
        </div>
      )}
    </div>
  );
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-800 rounded p-2 text-center">
      <div className="text-xs text-gray-400">{label}</div>
      <div className="font-semibold">{value}</div>
    </div>
  );
}

function CharacterForm({
  data,
  onChange,
  onSave,
  onCancel,
}: {
  data: Partial<Character>;
  onChange: (d: Partial<Character>) => void;
  onSave: () => void;
  onCancel: () => void;
}) {
  function set(key: keyof Character, value: unknown) {
    onChange({ ...data, [key]: value });
  }

  return (
    <div>
      <h2 className="text-xl font-bold text-red-300 mb-4">
        {data.id ? "Edit Character" : "New Character"}
      </h2>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <Label>Character Name</Label>
          <Input value={data.name ?? ""} onChange={(v) => set("name", v)} />
        </div>
        <div>
          <Label>Player Name</Label>
          <Input value={data.player_name ?? ""} onChange={(v) => set("player_name", v)} />
        </div>
        <div>
          <Label>Class</Label>
          <select
            className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm"
            value={data.character_class ?? "Fighter"}
            onChange={(e) => set("character_class", e.target.value)}
          >
            {CLASSES.map((c) => <option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <Label>Level</Label>
          <NumInput value={data.level ?? 1} onChange={(v) => set("level", v)} min={1} max={20} />
        </div>
        <div>
          <Label>Race</Label>
          <Input value={data.race ?? ""} onChange={(v) => set("race", v)} />
        </div>
        <div>
          <Label>Subclass (optional)</Label>
          <Input value={data.subclass ?? ""} onChange={(v) => set("subclass", v)} />
        </div>
      </div>

      <h3 className="text-gray-400 text-sm font-semibold mb-2">Combat Stats</h3>
      <div className="grid grid-cols-4 gap-3 mb-4">
        <div>
          <Label>Max HP</Label>
          <NumInput value={data.max_hp ?? 10} onChange={(v) => set("max_hp", v)} />
        </div>
        <div>
          <Label>Current HP</Label>
          <NumInput value={data.current_hp ?? 10} onChange={(v) => set("current_hp", v)} />
        </div>
        <div>
          <Label>AC</Label>
          <NumInput value={data.ac ?? 10} onChange={(v) => set("ac", v)} />
        </div>
        <div>
          <Label>Initiative Bonus</Label>
          <NumInput value={data.initiative_bonus ?? 0} onChange={(v) => set("initiative_bonus", v)} min={-5} max={20} />
        </div>
        <div>
          <Label>Speed (ft.)</Label>
          <NumInput value={data.speed ?? 30} onChange={(v) => set("speed", v)} />
        </div>
        <div>
          <Label>Passive Perception</Label>
          <NumInput value={data.passive_perception ?? 10} onChange={(v) => set("passive_perception", v)} />
        </div>
      </div>

      <h3 className="text-gray-400 text-sm font-semibold mb-2">Ability Scores</h3>
      <div className="grid grid-cols-6 gap-2 mb-4">
        {(["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"] as const).map((stat) => (
          <div key={stat} className="text-center">
            <Label>{stat.slice(0, 3).toUpperCase()}</Label>
            <NumInput value={(data[stat] as number) ?? 10} onChange={(v) => set(stat, v)} min={1} max={30} />
          </div>
        ))}
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
        <button onClick={onSave} className="bg-red-800 hover:bg-red-700 text-white px-4 py-2 rounded text-sm font-medium">Save</button>
        <button onClick={onCancel} className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm font-medium">Cancel</button>
      </div>
    </div>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return <div className="text-xs text-gray-400 mb-1">{children}</div>;
}

function Input({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <input
      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-red-600"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  );
}

function NumInput({ value, onChange, min = 0, max = 999 }: { value: number; onChange: (v: number) => void; min?: number; max?: number }) {
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
