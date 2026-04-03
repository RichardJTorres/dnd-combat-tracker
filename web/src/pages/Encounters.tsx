import { useEffect, useState } from "react";

interface Encounter {
  id: number;
  name: string;
  description: string | null;
}

interface Creature {
  id: number;
  name: string;
  cr: number;
  hp: number;
  ac: number;
  creature_type: string;
}

interface Character {
  id: number;
  name: string;
  character_class: string;
  level: number;
  max_hp: number;
  ac: number;
  initiative_bonus: number;
}

interface Participant {
  id: number;
  participant_type: "creature" | "character";
  creature_id: number | null;
  character_id: number | null;
  quantity: number;
}

function crLabel(cr: number): string {
  const m: Record<number, string> = { 0.125: "1/8", 0.25: "1/4", 0.5: "1/2" };
  return m[cr] ?? String(Math.round(cr));
}

export default function Encounters({
  onLaunchCombat,
}: {
  onLaunchCombat: (sessionId: number) => void;
}) {
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [selected, setSelected] = useState<Encounter | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [creatures, setCreatures] = useState<Creature[]>([]);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [newName, setNewName] = useState("");
  const [addType, setAddType] = useState<"creature" | "character">("creature");
  const [addId, setAddId] = useState<number | "">("");
  const [addQty, setAddQty] = useState(1);
  const [launching, setLaunching] = useState(false);

  async function loadEncounters() {
    const r = await fetch("/api/encounters");
    setEncounters(await r.json());
  }

  async function loadParticipants(encId: number) {
    const r = await fetch(`/api/encounters/${encId}/participants`);
    setParticipants(await r.json());
  }

  async function loadOptions() {
    const [cr, ch] = await Promise.all([
      fetch("/api/creatures").then((r) => r.json()),
      fetch("/api/characters").then((r) => r.json()),
    ]);
    setCreatures(cr);
    setCharacters(ch);
  }

  useEffect(() => {
    loadEncounters();
    loadOptions();
  }, []);

  async function selectEncounter(enc: Encounter) {
    setSelected(enc);
    await loadParticipants(enc.id);
  }

  async function createEncounter() {
    if (!newName.trim()) return;
    await fetch("/api/encounters", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newName.trim() }),
    });
    setNewName("");
    loadEncounters();
  }

  async function deleteEncounter(id: number) {
    if (!confirm("Delete this encounter?")) return;
    await fetch(`/api/encounters/${id}`, { method: "DELETE" });
    if (selected?.id === id) { setSelected(null); setParticipants([]); }
    loadEncounters();
  }

  async function addParticipant() {
    if (!selected || addId === "") return;
    const data: Record<string, unknown> = { participant_type: addType };
    if (addType === "creature") {
      data.creature_id = addId;
      data.quantity = addQty;
    } else {
      data.character_id = addId;
    }
    await fetch(`/api/encounters/${selected.id}/participants`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    loadParticipants(selected.id);
  }

  async function removeParticipant(pid: number) {
    if (!selected) return;
    await fetch(`/api/encounters/${selected.id}/participants/${pid}`, {
      method: "DELETE",
    });
    loadParticipants(selected.id);
  }

  async function launchCombat() {
    if (!selected) return;
    setLaunching(true);

    const combatants: Record<string, unknown>[] = [];

    for (const p of participants) {
      if (p.participant_type === "creature" && p.creature_id) {
        const creature = creatures.find((c) => c.id === p.creature_id);
        if (!creature) continue;
        for (let i = 0; i < p.quantity; i++) {
          const label = p.quantity > 1 ? ` ${i + 1}` : "";
          combatants.push({
            name: `${creature.name}${label}`,
            combatant_type: "creature",
            source_id: creature.id,
            initiative: 0,
            max_hp: creature.hp,
            current_hp: creature.hp,
            ac: creature.ac,
          });
        }
      } else if (p.participant_type === "character" && p.character_id) {
        const char = characters.find((c) => c.id === p.character_id);
        if (!char) continue;
        combatants.push({
          name: char.name,
          combatant_type: "character",
          source_id: char.id,
          initiative: 0,
          max_hp: char.max_hp,
          current_hp: char.max_hp,
          ac: char.ac,
        });
      }
    }

    const r = await fetch("/api/combat/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ encounter_id: selected.id, combatants }),
    });
    const data = await r.json();
    setLaunching(false);
    onLaunchCombat(data.session.id);
  }

  function participantLabel(p: Participant): string {
    if (p.participant_type === "creature") {
      const c = creatures.find((c) => c.id === p.creature_id);
      return c ? `${c.name} ×${p.quantity} (CR ${crLabel(c.cr)}, HP ${c.hp}, AC ${c.ac})` : "Unknown creature";
    }
    const ch = characters.find((c) => c.id === p.character_id);
    return ch ? `${ch.name} (Lvl ${ch.level} ${ch.character_class})` : "Unknown character";
  }

  return (
    <div className="flex gap-4">
      {/* Encounter list */}
      <div className="w-64 flex-shrink-0 flex flex-col gap-3">
        <div className="flex gap-2">
          <input
            className="input-fantasy flex-1"
            placeholder="New encounter name..."
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && createEncounter()}
          />
          <button
            onClick={createEncounter}
            className="bg-crimson-700 hover:bg-crimson-600 text-parchment-50 text-sm px-3 py-1.5 rounded"
          >
            +
          </button>
        </div>

        <div className="space-y-1 overflow-y-auto scrollbar-thin">
          {encounters.length === 0 && (
            <p className="text-ink-400 italic text-sm text-center py-8">No encounters yet</p>
          )}
          {encounters.map((enc) => (
            <button
              key={enc.id}
              onClick={() => selectEncounter(enc)}
              className={`w-full text-left px-3 py-2 rounded border text-sm transition-colors ${
                selected?.id === enc.id
                  ? "bg-crimson-900/30 border-crimson-500 text-crimson-400"
                  : "bg-parchment-100 border-leather-600 hover:border-leather-400 text-ink-800"
              }`}
            >
              {enc.name}
            </button>
          ))}
        </div>
      </div>

      {/* Encounter detail */}
      <div className="flex-1 panel p-5">
        {!selected ? (
          <div className="text-ink-400 italic text-center mt-20">
            Select or create an encounter
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-display font-bold text-crimson-600">{selected.name}</h2>
              <div className="flex gap-2">
                <button
                  onClick={launchCombat}
                  disabled={launching || participants.length === 0}
                  className="bg-crimson-600 hover:bg-crimson-500 disabled:opacity-40 text-parchment-50 px-4 py-2 rounded text-sm font-display uppercase tracking-wider"
                >
                  {launching ? "Starting..." : "⚔️ Launch Combat"}
                </button>
                <button
                  onClick={() => deleteEncounter(selected.id)}
                  className="bg-parchment-300 hover:bg-parchment-400 text-ink-900 border border-leather-500 px-3 py-2 rounded text-sm"
                >
                  Delete
                </button>
              </div>
            </div>

            {/* Participants */}
            <h3 className="text-ink-600 text-sm font-display font-semibold mb-2 uppercase tracking-wide">
              Participants ({participants.length})
            </h3>
            <div className="space-y-1 mb-4">
              {participants.length === 0 && (
                <p className="text-ink-400 italic text-sm">No participants yet. Add creatures or characters below.</p>
              )}
              {participants.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between bg-parchment-200 border border-leather-600 rounded px-3 py-2 text-sm"
                >
                  <span className={p.participant_type === "character" ? "text-azure-400" : "text-ink-800"}>
                    {p.participant_type === "character" ? "👤 " : "👾 "}
                    {participantLabel(p)}
                  </span>
                  <button
                    onClick={() => removeParticipant(p.id)}
                    className="text-ink-400 hover:text-crimson-500 text-xs ml-2"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>

            {/* Add participant */}
            <div className="panel-inset p-3">
              <h4 className="text-xs text-ink-600 font-display font-semibold uppercase tracking-wide mb-2">Add Participant</h4>
              <div className="flex gap-2 flex-wrap">
                <select
                  className="input-fantasy"
                  value={addType}
                  onChange={(e) => {
                    setAddType(e.target.value as "creature" | "character");
                    setAddId("");
                  }}
                >
                  <option value="creature">Creature</option>
                  <option value="character">Character</option>
                </select>

                <select
                  className="input-fantasy flex-1"
                  value={addId}
                  onChange={(e) => setAddId(parseInt(e.target.value) || "")}
                >
                  <option value="">Select...</option>
                  {addType === "creature"
                    ? creatures.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name} (CR {crLabel(c.cr)})
                        </option>
                      ))
                    : characters.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                        </option>
                      ))}
                </select>

                {addType === "creature" && (
                  <input
                    type="number"
                    className="input-fantasy w-16"
                    value={addQty}
                    min={1}
                    max={20}
                    onChange={(e) => setAddQty(parseInt(e.target.value) || 1)}
                    title="Quantity"
                  />
                )}

                <button
                  onClick={addParticipant}
                  disabled={addId === ""}
                  className="bg-crimson-700 hover:bg-crimson-600 disabled:opacity-40 text-parchment-50 px-3 py-1.5 rounded text-sm"
                >
                  Add
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
