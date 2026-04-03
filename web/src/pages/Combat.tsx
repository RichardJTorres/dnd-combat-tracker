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
  if (pct <= 0)   return "bg-parchment-400 text-ink-400";
  if (pct < 0.25) return "bg-hp-critical text-parchment-100";
  if (pct < 0.5)  return "bg-hp-low text-parchment-100";
  if (pct < 0.75) return "bg-hp-medium text-parchment-50";
  return                 "bg-hp-good text-parchment-50";
}

function hpBarColor(current: number, max: number): string {
  const pct = max > 0 ? current / max : 0;
  if (pct < 0.25) return "bg-hpbar-critical";
  if (pct < 0.5)  return "bg-hpbar-low";
  if (pct < 0.75) return "bg-hpbar-medium";
  return                 "bg-hpbar-good";
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
        <div className="text-ink-400 italic mb-4">No active combat session.</div>
        <p className="text-ink-400 text-sm">
          Go to <strong className="text-ink-600 font-display">Encounters</strong> to launch a combat.
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
      <div className="flex items-center justify-between mb-4 bg-parchment-200 border-2 border-leather-400 rounded-lg px-4 py-3 shadow-md">
        <div className="flex items-center gap-6">
          <div>
            <div className="text-xs text-ink-400 font-display uppercase tracking-widest">Round</div>
            <div className="text-3xl font-display font-bold text-crimson-600">{session.round_number}</div>
          </div>
          {currentCombatant && (
            <div>
              <div className="text-xs text-ink-400 font-display uppercase tracking-widest">Current Turn</div>
              <div className="text-lg font-display font-semibold text-gold-500">
                {currentCombatant.name}
              </div>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={nextTurn}
            className="bg-crimson-700 hover:bg-crimson-600 text-parchment-50 px-5 py-2 rounded font-display uppercase tracking-wide shadow-sm"
          >
            Next Turn →
          </button>
          <button
            onClick={endCombat}
            className="bg-parchment-300 hover:bg-parchment-400 text-ink-900 border border-leather-500 px-4 py-2 rounded text-sm"
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
              className={`bg-parchment-100 border rounded-lg p-3 transition-all ${
                !c.is_active
                  ? "opacity-40 border-leather-700"
                  : isCurrent
                  ? "border-gold-400 shadow-[0_0_14px_rgba(201,162,39,0.35)] bg-gold-500/5"
                  : "border-leather-600"
              }`}
            >
              <div className="flex items-center gap-3">
                {/* Initiative */}
                <div className="text-center w-14 flex-shrink-0">
                  <div className="text-xs text-ink-400 font-display uppercase">Init</div>
                  <input
                    type="number"
                    className="w-full bg-parchment-300 border border-leather-500 rounded px-1 py-0.5 text-center text-sm font-bold text-ink-900 focus:outline-none focus:border-gold-400"
                    value={initiativeInputs[c.id] ?? c.initiative}
                    onChange={(e) => updateInitiative(c.id, e.target.value)}
                    onBlur={() => commitInitiative(c.id)}
                  />
                </div>

                {/* Name */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`font-display font-semibold truncate ${isCurrent ? "text-gold-500" : c.combatant_type === "character" ? "text-azure-400" : "text-ink-800"}`}>
                      {c.combatant_type === "character" ? "👤 " : "👾 "}
                      {c.name}
                    </span>
                    {isCurrent && (
                      <span className="text-xs bg-gold-700 text-gold-300 px-1.5 py-0.5 rounded font-display uppercase">
                        ACTIVE
                      </span>
                    )}
                  </div>
                  {conditions.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {conditions.map((cond) => (
                        <span
                          key={cond}
                          className="text-xs bg-arcane-800 text-arcane-200 px-1.5 py-0.5 rounded italic"
                        >
                          {cond}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* AC */}
                <div className="text-center w-12 flex-shrink-0">
                  <div className="text-xs text-ink-400 font-display uppercase">AC</div>
                  <div className="font-display font-bold text-ink-900">{c.ac}</div>
                </div>

                {/* HP */}
                <div className="w-44 flex-shrink-0">
                  <div className="flex items-center justify-between mb-1">
                    <div className="text-xs text-ink-400 font-display uppercase">HP</div>
                    <div className={`text-sm font-bold px-1.5 py-0.5 rounded ${hpColor(c.current_hp, c.max_hp)}`}>
                      {c.current_hp} / {c.max_hp}
                      {c.temp_hp > 0 && <span className="text-azure-300"> (+{c.temp_hp})</span>}
                    </div>
                  </div>
                  <div className="h-2 bg-parchment-400 rounded overflow-hidden border border-leather-600">
                    <div
                      className={`h-full transition-all ${hpBarColor(c.current_hp, c.max_hp)}`}
                      style={{ width: hpBarWidth(c.current_hp, c.max_hp) }}
                    />
                  </div>
                </div>

                {/* HP delta input */}
                <div className="flex gap-1 flex-shrink-0">
                  <input
                    type="text"
                    className="w-16 bg-parchment-300 border border-leather-500 rounded px-2 py-1 text-sm text-ink-900 text-center focus:outline-none focus:border-crimson-500"
                    placeholder="±HP"
                    value={hpDelta[c.id] ?? ""}
                    onChange={(e) => setHpDelta((prev) => ({ ...prev, [c.id]: e.target.value }))}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") applyHpDelta(c);
                    }}
                  />
                  <button
                    onClick={() => applyHpDelta(c)}
                    className="bg-parchment-300 hover:bg-parchment-400 text-ink-900 border border-leather-500 px-2 py-1 rounded text-xs"
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
                      ? "bg-arcane-700 text-arcane-200"
                      : "bg-parchment-200 hover:bg-parchment-300 text-ink-600 border border-leather-500"
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
                      ? "bg-parchment-200 hover:bg-crimson-900/30 text-ink-400 border border-leather-600"
                      : "bg-parchment-300 text-ink-400 hover:bg-parchment-400 border border-leather-600"
                  }`}
                  title={c.is_active ? "Remove from combat" : "Restore to combat"}
                >
                  {c.is_active ? "✕" : "↩"}
                </button>
              </div>

              {/* Conditions panel */}
              {conditionsOpen === c.id && (
                <div className="mt-3 pt-3 border-t border-leather-600">
                  <div className="text-xs text-ink-400 font-display uppercase tracking-wide mb-2">Toggle conditions:</div>
                  <div className="flex flex-wrap gap-1">
                    {CONDITIONS.map((cond) => {
                      const active = conditions.includes(cond);
                      return (
                        <button
                          key={cond}
                          onClick={() => toggleCondition(c, cond)}
                          className={`text-xs px-2 py-1 rounded transition-colors ${
                            active
                              ? "bg-arcane-700 text-arcane-200"
                              : "bg-parchment-300 text-ink-600 hover:bg-parchment-400 border border-leather-600"
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
          <h3 className="text-xs text-ink-400 font-display uppercase tracking-wide mb-2">Removed from combat</h3>
          <div className="space-y-1">
            {combatants
              .filter((c) => !c.is_active)
              .map((c) => (
                <div key={c.id} className="flex items-center gap-2 text-sm text-ink-400 bg-parchment-100 rounded px-3 py-1.5 border border-leather-700 opacity-50">
                  <span>{c.name}</span>
                  <button
                    onClick={() => toggleActive(c)}
                    className="ml-auto text-xs text-ink-400 hover:text-crimson-500"
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
