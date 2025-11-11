/**
 * Library stats pills component.
 *
 * Displays library statistics as pill-shaped badges.
 * Follows SRP by focusing solely on stats presentation.
 * Follows SOC by separating stats display from data fetching.
 * Follows IOC by using configuration-based pill generation.
 * Follows Open/Closed Principle - open for extension via config.
 */

import type { LibraryStats } from "@/services/libraryStatsService";
import { LibraryStatPill } from "./LibraryStatPill";
import { LIBRARY_STATS_PILL_CONFIG } from "./pillConfig";

export interface LibraryStatsPillsProps {
  /** Library statistics to display. */
  stats: LibraryStats;
}

/**
 * Library stats pills component.
 *
 * Displays library statistics as rounded pill badges.
 * Uses configuration to generate pills, making it easy to add new ones.
 *
 * Parameters
 * ----------
 * props : LibraryStatsPillsProps
 *     Component props including stats data.
 */
export function LibraryStatsPills({ stats }: LibraryStatsPillsProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {LIBRARY_STATS_PILL_CONFIG.map((config) => {
        const value = stats[config.statKey];
        const formattedValue = config.formatter(value);

        return (
          <LibraryStatPill
            key={config.statKey}
            value={formattedValue}
            label={config.label}
          />
        );
      })}
    </div>
  );
}
