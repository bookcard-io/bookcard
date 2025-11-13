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

import { useMemo } from "react";
import type { Shelf } from "@/types/shelf";

/** Maximum number of recent shelves to return. */
const MAX_RECENT_SHELVES = 5;

/**
 * Hook for getting recently created shelves.
 *
 * Returns the most recently created shelves sorted by creation date.
 * Follows SRP by handling only shelf sorting and filtering.
 * Follows DRY by centralizing the recent shelves calculation logic.
 *
 * Parameters
 * ----------
 * shelves : Shelf[]
 *     Full list of shelves to filter and sort.
 *
 * Returns
 * -------
 * Shelf[]
 *     Top 5 most recently created shelves (most recent first).
 */
export function useRecentCreatedShelves(shelves: Shelf[]): Shelf[] {
  return useMemo(() => {
    return [...shelves]
      .sort((a, b) => {
        const dateA = new Date(a.created_at).getTime();
        const dateB = new Date(b.created_at).getTime();
        return dateB - dateA; // Descending order
      })
      .slice(0, MAX_RECENT_SHELVES);
  }, [shelves]);
}
