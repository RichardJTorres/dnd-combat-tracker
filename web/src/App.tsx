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
      <header className="bg-gray-900 border-b border-gray-800 px-4 py-3 flex items-center gap-4">
        <h1 className="text-xl font-bold text-red-400 tracking-wide">
          ⚔️ D&D Combat Tracker
        </h1>
        <nav className="flex gap-1 ml-4">
          {NAV.map((n) => (
            <button
              key={n.id}
              onClick={() => setPage(n.id)}
              className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
                page === n.id
                  ? "bg-red-900/60 text-red-200 border border-red-700"
                  : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
              }`}
            >
              {n.icon} {n.label}
            </button>
          ))}
        </nav>
      </header>

      {/* Main content */}
      <main className="flex-1 p-4">
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
