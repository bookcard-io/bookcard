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
 * Custom hook for fetching library statistics.
 *
 * Manages loading state and caching for multiple library stats.
 * Follows SRP by handling only stats fetching concerns.
 * Follows IOC by accepting libraries and returning state/actions.
 */

import { useEffect, useRef, useState } from "react";
import {
  fetchLibraryStats,
  type LibraryStats,
} from "@/services/libraryStatsService";

export interface UseLibraryStatsResult {
  /** Map of library ID to stats data. */
  stats: Record<number, LibraryStats | null>;
  /** Map of library ID to loading state. */
  loadingStats: Record<number, boolean>;
}

export interface Library {
  id: number;
}

/**
 * Custom hook for fetching library statistics.
 *
 * Fetches stats for all provided libraries, caching results to avoid
 * redundant API calls. Handles loading states per library.
 *
 * Parameters
 * ----------
 * libraries : Library[]
 *     List of libraries to fetch stats for.
 *
 * Returns
 * -------
 * UseLibraryStatsResult
 *     Stats data and loading states.
 */
export function useLibraryStats(libraries: Library[]): UseLibraryStatsResult {
  const [stats, setStats] = useState<Record<number, LibraryStats | null>>({});
  const [loadingStats, setLoadingStats] = useState<Record<number, boolean>>({});
  const fetchedIdsRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    const fetchStatsForLibraries = async () => {
      for (const lib of libraries) {
        if (fetchedIdsRef.current.has(lib.id)) {
          continue; // Already loaded or failed
        }

        fetchedIdsRef.current.add(lib.id);
        setLoadingStats((prev) => ({ ...prev, [lib.id]: true }));

        const data = await fetchLibraryStats(lib.id);
        setStats((prev) => ({ ...prev, [lib.id]: data }));
        setLoadingStats((prev) => ({ ...prev, [lib.id]: false }));
      }
    };

    void fetchStatsForLibraries();
  }, [libraries]);

  return { stats, loadingStats };
}
