export type DifficultyTier = "Trivial" | "Easy" | "Medium" | "Hard" | "Deadly";

export interface DifficultyInput {
  characterLevels: number[];
  creatures: { cr: number; quantity: number }[];
}

export interface DifficultyResult {
  tier: DifficultyTier;
  rawXp: number;
  adjustedXp: number;
  partyThresholds: { easy: number; medium: number; hard: number; deadly: number };
  monsterCount: number;
  multiplier: number;
}

const CR_XP: Record<number, number> = {
  0: 10, 0.125: 25, 0.25: 50, 0.5: 100,
  1: 200, 2: 450, 3: 700, 4: 1100, 5: 1800,
  6: 2300, 7: 2900, 8: 3900, 9: 5000, 10: 5900,
  11: 7200, 12: 8400, 13: 10000, 14: 11500, 15: 13000,
  16: 15000, 17: 18000, 18: 20000, 19: 22000, 20: 25000,
  21: 33000, 22: 41000, 23: 50000, 24: 62000, 25: 75000,
  26: 90000, 27: 105000, 28: 120000, 29: 135000, 30: 155000,
};

// [easy, medium, hard, deadly]
const LEVEL_THRESHOLDS: Record<number, [number, number, number, number]> = {
  1:  [25,   50,   75,   100],
  2:  [50,   100,  150,  200],
  3:  [75,   150,  225,  400],
  4:  [125,  250,  375,  500],
  5:  [250,  500,  750,  1100],
  6:  [300,  600,  900,  1400],
  7:  [350,  750,  1100, 1700],
  8:  [450,  900,  1400, 2100],
  9:  [550,  1100, 1600, 2400],
  10: [600,  1200, 1900, 2800],
  11: [800,  1600, 2400, 3600],
  12: [1000, 2000, 3000, 4500],
  13: [1100, 2200, 3400, 5100],
  14: [1250, 2500, 3800, 5700],
  15: [1400, 2800, 4300, 6400],
  16: [1600, 3200, 4800, 7200],
  17: [2000, 3900, 5900, 8800],
  18: [2100, 4200, 6300, 9500],
  19: [2400, 4900, 7300, 10900],
  20: [2800, 5700, 8500, 12700],
};

function getMultiplier(monsterCount: number): number {
  if (monsterCount <= 1) return 1;
  if (monsterCount === 2) return 1.5;
  if (monsterCount <= 6) return 2;
  if (monsterCount <= 10) return 2.5;
  if (monsterCount <= 14) return 3;
  return 4;
}

export function calculateDifficulty(input: DifficultyInput): DifficultyResult {
  const monsterCount = input.creatures.reduce((sum, c) => sum + c.quantity, 0);
  const rawXp = input.creatures.reduce(
    (sum, c) => sum + (CR_XP[c.cr] ?? 0) * c.quantity,
    0
  );
  const multiplier = getMultiplier(monsterCount);
  const adjustedXp = Math.floor(rawXp * multiplier);

  const partyThresholds = input.characterLevels.reduce(
    (acc, level) => {
      const t = LEVEL_THRESHOLDS[Math.min(Math.max(level, 1), 20)] ?? LEVEL_THRESHOLDS[1];
      return {
        easy:   acc.easy   + t[0],
        medium: acc.medium + t[1],
        hard:   acc.hard   + t[2],
        deadly: acc.deadly + t[3],
      };
    },
    { easy: 0, medium: 0, hard: 0, deadly: 0 }
  );

  let tier: DifficultyTier;
  if (adjustedXp >= partyThresholds.deadly) tier = "Deadly";
  else if (adjustedXp >= partyThresholds.hard) tier = "Hard";
  else if (adjustedXp >= partyThresholds.medium) tier = "Medium";
  else if (adjustedXp >= partyThresholds.easy) tier = "Easy";
  else tier = "Trivial";

  return { tier, rawXp, adjustedXp, partyThresholds, monsterCount, multiplier };
}
