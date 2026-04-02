import { useEffect, useState } from "react";

interface CombatSession {
  id: number;
  encounter_id: number;
  round_number: number;
  current_turn_index: number;
  is_active: boolean;
}

interface Combatant {
  id: number;
  session_id: number;
  name: string;
  combatant_type: "creature" | "character";
  initiative: number;
  max_hp: number;
  current_hp: number;
  temp_hp: number;
  ac: number;
  conditions: string; // JSON array
  is_active: boolean;
  sort_order: number;
  notes: string | null;
}

const CONDITIONS = [
  "Blinded", "Charmed", "Deafened", "Exhaustion", "Frightened",
  "Grappled", "Incapacitated", "Invisible", "Paralyzed", "Petrified",
  "Poisoned", "Prone", "Restrained", "Stunned", "Unconscious",
];

function hpColor(current: number, max: number): string {
  const pct = max > 0 ? current / max : 0;
  if (pct <= 0) return "bg-gray-700 text-gray-500";
  if (pct < 0.25) return "bg-red-900 text-red-300";
  if (pct < 0.5) return "bg-orange-900 text-orange-300";
  if (pct < 0.75) return "bg-yellow-900 text-yellow-300";
  return "bg-green-900 text-green-300";
}

function hpBarWidth(current: number, max: number): string {
  const pct = max > 0 ? Math.max(0, Math.min(100, (current / max) * 100)) : 0;
  return `${pct}%`;
}

export default function Combat({
  sessionId,
  onSessionChange,
}: {
  sessionId: number | null;
  onSessionChange: (id: number | null) => void;
}) {
  const [session, setSession] = useState<CombatSession | null>(null);
  const [combatants, setCombatants] = useState<Combatant[]>([]);
  const [hpDelta, setHpDelta] = useState<Record<number, string>>({});
  const [initiativeInputs, setInitiativeInputs] = useState<Record<number, string>>({});
  const [conditionsOpen, setConditionsOpen] = useState<number | null>(null);

  async function load(id: number) {
    const r = await fetch(`/api/combat/sessions/${id}`);
    if (!r.ok) return;
    const data = await r.json();
    setSession(data.session);
    setCombatants(data.combatants);
    // Init initiative inputs
    const inits: Record<number, string> = {};
    for (const c of data.combatants) {
      inits[c.id] = String(c.initiative);
    }
    setInitiativeInputs(inits);
  }

  useEffect(() => {
    if (sessionId) load(sessionId);
    else { setSession(null); setCombatants([]); }
  }, [sessionId]);

  async function nextTurn() {
    if (!session) return;
    const r = await fetch(`/api/combat/sessions/${session.id}/next-turn`, { method: "POST" });
    const data = await r.json();
    setSession(data.session);
    setCombatants(data.combatants);
  }

  async function endCombat() {
    if (!session || !confirm("End this combat?")) return;
    await fetch(`/api/combat/sessions/${session.id}/end`, { method: "POST" });
    onSessionChange(null);
    setSession(null);
    setCombatants([]);
  }

  async function applyHpDelta(combatant: Combatant) {
    const raw = hpDelta[combatant.id] ?? "";
    if (!raw.trim()) return;
    const delta = parseInt(raw);
    if (isNaN(delta)) return;
    const newHp = Math.max(0, Math.min(combatant.max_hp, combatant.current_hp + delta));
    await updateCombatant(combatant.id, { current_hp: newHp });
    setHpDelta((prev) => ({ ...prev, [combatant.id]: "" }));
  }

  async function updateInitiative(combatantId: number, value: string) {
    setInitiativeInputs((prev) => ({ ...prev, [combatantId]: value }));
  }

  async function commitInitiative(combatantId: number) {
    const raw = initiativeInputs[combatantId];
    const val = parseInt(raw);
    if (!isNaN(val)) {
      await updateCombatant(combatantId, { initiative: val });
    }
  }

  async function toggleCondition(combatant: Combatant, condition: string) {
    const current = JSON.parse(combatant.conditions) as string[];
    const next = current.includes(condition)
      ? current.filter((c) => c !== condition)
      : [...current, condition];
    await updateCombatant(combatant.id, { conditions: JSON.stringify(next) });
  }

  async function toggleActive(combatant: Combatant) {
    await updateCombatant(combatant.id, { is_active: !combatant.is_active });
  }

  async function updateCombatant(id: number, data: Record<string, unknown>) {
    const r = await fetch(`/api/combat/combatants/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const updated = await r.json();
    setCombatants((prev) => prev.map((c) => (c.id === id ? updated : c)));
  }

  if (!session) {
    return (
      <div className="text-center mt-20">
        <div className="text-gray-500 mb-4">No active combat session.</div>
        <p className="text-gray-600 text-sm">
          Go to <strong className="text-gray-400">Encounters</strong> to launch a combat.
        </p>
      </div>
    );
  }

  const activeCombatants = combatants.filter((c) => c.is_active);
  const currentCombatant = activeCombatants.find(
    (c) => c.sort_order === session.current_turn_index
  );

  return (
    <div className="max-w-5xl mx-auto">
      {/* Combat header */}
      <div className="flex items-center justify-between mb-4 bg-gray-900 border border-gray-800 rounded-lg px-4 py-3">
        <div className="flex items-center gap-6">
          <div>
            <div className="text-xs text-gray-400">Round</div>
            <div className="text-3xl font-bold text-red-400">{session.round_number}</div>
          </div>
          {currentCombatant && (
            <div>
              <div className="text-xs text-gray-400">Current Turn</div>
              <div className="text-lg font-semibold text-yellow-300">
                {currentCombatant.name}
              </div>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={nextTurn}
            className="bg-red-700 hover:bg-red-600 text-white px-5 py-2 rounded font-medium"
          >
            Next Turn →
          </button>
          <button
            onClick={endCombat}
            className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm"
          >
            End Combat
          </button>
        </div>
      </div>

      {/* Combatant rows */}
      <div className="space-y-2">
        {combatants.map((c) => {
          const isCurrent = c.sort_order === session.current_turn_index && c.is_active;
          const conditions = JSON.parse(c.conditions) as string[];

          return (
            <div
              key={c.id}
              className={`bg-gray-900 border rounded-lg p-3 transition-all ${
                !c.is_active
                  ? "opacity-40 border-gray-800"
                  : isCurrent
                  ? "border-yellow-600 shadow-[0_0_12px_rgba(202,138,4,0.2)]"
                  : "border-gray-800"
              }`}
            >
              <div className="flex items-center gap-3">
                {/* Initiative */}
                <div className="text-center w-14 flex-shrink-0">
                  <div className="text-xs text-gray-500">Init</div>
                  <input
                    type="number"
                    className="w-full bg-gray-800 border border-gray-700 rounded px-1 py-0.5 text-center text-sm font-bold focus:outline-none focus:border-yellow-600"
                    value={initiativeInputs[c.id] ?? c.initiative}
                    onChange={(e) => updateInitiative(c.id, e.target.value)}
                    onBlur={() => commitInitiative(c.id)}
                  />
                </div>

                {/* Name */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`font-semibold truncate ${isCurrent ? "text-yellow-200" : c.combatant_type === "character" ? "text-blue-300" : "text-gray-200"}`}>
                      {c.combatant_type === "character" ? "👤 " : "👾 "}
                      {c.name}
                    </span>
                    {isCurrent && (
                      <span className="text-xs bg-yellow-800 text-yellow-200 px-1.5 py-0.5 rounded">
                        ACTIVE
                      </span>
                    )}
                  </div>
                  {conditions.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {conditions.map((cond) => (
                        <span
                          key={cond}
                          className="text-xs bg-purple-900 text-purple-200 px-1.5 py-0.5 rounded"
                        >
                          {cond}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* AC */}
                <div className="text-center w-12 flex-shrink-0">
                  <div className="text-xs text-gray-500">AC</div>
                  <div className="font-bold">{c.ac}</div>
                </div>

                {/* HP */}
                <div className="w-44 flex-shrink-0">
                  <div className="flex items-center justify-between mb-1">
                    <div className="text-xs text-gray-500">HP</div>
                    <div className={`text-sm font-bold px-1.5 py-0.5 rounded ${hpColor(c.current_hp, c.max_hp)}`}>
                      {c.current_hp} / {c.max_hp}
                      {c.temp_hp > 0 && <span className="text-blue-300"> (+{c.temp_hp})</span>}
                    </div>
                  </div>
                  <div className="h-2 bg-gray-700 rounded overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        c.current_hp / c.max_hp < 0.25
                          ? "bg-red-500"
                          : c.current_hp / c.max_hp < 0.5
                          ? "bg-orange-500"
                          : c.current_hp / c.max_hp < 0.75
                          ? "bg-yellow-500"
                          : "bg-green-500"
                      }`}
                      style={{ width: hpBarWidth(c.current_hp, c.max_hp) }}
                    />
                  </div>
                </div>

                {/* HP delta input */}
                <div className="flex gap-1 flex-shrink-0">
                  <input
                    type="text"
                    className="w-16 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-center focus:outline-none focus:border-red-600"
                    placeholder="±HP"
                    value={hpDelta[c.id] ?? ""}
                    onChange={(e) => setHpDelta((prev) => ({ ...prev, [c.id]: e.target.value }))}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") applyHpDelta(c);
                    }}
                  />
                  <button
                    onClick={() => applyHpDelta(c)}
                    className="bg-gray-700 hover:bg-gray-600 text-white px-2 py-1 rounded text-xs"
                    title="Apply HP change"
                  >
                    ✓
                  </button>
                </div>

                {/* Conditions button */}
                <button
                  onClick={() => setConditionsOpen(conditionsOpen === c.id ? null : c.id)}
                  className={`px-2 py-1 rounded text-xs flex-shrink-0 ${
                    conditions.length > 0
                      ? "bg-purple-800 text-purple-200"
                      : "bg-gray-700 hover:bg-gray-600 text-gray-300"
                  }`}
                  title="Conditions"
                >
                  ⚡
                </button>

                {/* Toggle dead/active */}
                <button
                  onClick={() => toggleActive(c)}
                  className={`px-2 py-1 rounded text-xs flex-shrink-0 ${
                    c.is_active
                      ? "bg-gray-700 hover:bg-red-900 text-gray-400"
                      : "bg-gray-800 text-gray-600 hover:bg-gray-700"
                  }`}
                  title={c.is_active ? "Remove from combat" : "Restore to combat"}
                >
                  {c.is_active ? "✕" : "↩"}
                </button>
              </div>

              {/* Conditions panel */}
              {conditionsOpen === c.id && (
                <div className="mt-3 pt-3 border-t border-gray-800">
                  <div className="text-xs text-gray-400 mb-2">Toggle conditions:</div>
                  <div className="flex flex-wrap gap-1">
                    {CONDITIONS.map((cond) => {
                      const active = conditions.includes(cond);
                      return (
                        <button
                          key={cond}
                          onClick={() => toggleCondition(c, cond)}
                          className={`text-xs px-2 py-1 rounded transition-colors ${
                            active
                              ? "bg-purple-700 text-purple-100"
                              : "bg-gray-700 text-gray-400 hover:bg-gray-600"
                          }`}
                        >
                          {cond}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Inactive / dead combatants */}
      {combatants.some((c) => !c.is_active) && (
        <div className="mt-4">
          <h3 className="text-xs text-gray-500 mb-2">Removed from combat</h3>
          <div className="space-y-1">
            {combatants
              .filter((c) => !c.is_active)
              .map((c) => (
                <div key={c.id} className="flex items-center gap-2 text-sm text-gray-600 bg-gray-900 rounded px-3 py-1.5 border border-gray-800 opacity-50">
                  <span>{c.name}</span>
                  <button
                    onClick={() => toggleActive(c)}
                    className="ml-auto text-xs text-gray-500 hover:text-gray-300"
                  >
                    Restore
                  </button>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
