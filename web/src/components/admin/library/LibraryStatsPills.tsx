// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
