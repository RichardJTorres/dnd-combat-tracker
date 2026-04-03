import { useState } from "react";
import Bestiary from "./pages/Bestiary";
import Party from "./pages/Party";
import Encounters from "./pages/Encounters";
import Combat from "./pages/Combat";
import Settings from "./pages/Settings";

type Page = "bestiary" | "party" | "encounters" | "combat" | "settings";

const NAV: { id: Page; label: string; icon: string }[] = [
  { id: "bestiary", label: "Bestiary", icon: "📖" },
  { id: "party", label: "Party", icon: "⚔️" },
  { id: "encounters", label: "Encounters", icon: "🗺️" },
  { id: "combat", label: "Combat", icon: "🎲" },
  { id: "settings", label: "Settings", icon: "⚙️" },
];

export default function App() {
  const [page, setPage] = useState<Page>("bestiary");
  const [activeCombatSessionId, setActiveCombatSessionId] = useState<
    number | null
  >(null);

  function launchCombat(sessionId: number) {
    setActiveCombatSessionId(sessionId);
    setPage("combat");
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="bg-leather-700 border-b-2 border-leather-400 shadow-md px-4 py-3 flex items-center gap-4">
        <h1 className="text-xl font-display font-bold text-gold-400 tracking-widest uppercase">
          ⚔️ D&D Combat Tracker
        </h1>
        <nav className="flex gap-1 ml-4">
          {NAV.map((n) => (
            <button
              key={n.id}
              onClick={() => setPage(n.id)}
              className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
                page === n.id
                  ? "bg-parchment-100 text-ink-900 border border-gold-400"
                  : "text-parchment-200 hover:text-gold-300 hover:bg-leather-600"
              }`}
            >
              {n.icon} {n.label}
            </button>
          ))}
        </nav>
      </header>

      {/* Main content */}
      <main className="flex-1 p-4 bg-parchment-50">
        {page === "bestiary" && <Bestiary />}
        {page === "party" && <Party />}
        {page === "encounters" && <Encounters onLaunchCombat={launchCombat} />}
        {page === "combat" && (
          <Combat
            sessionId={activeCombatSessionId}
            onSessionChange={setActiveCombatSessionId}
          />
        )}
        {page === "settings" && <Settings />}
      </main>
    </div>
  );
}
