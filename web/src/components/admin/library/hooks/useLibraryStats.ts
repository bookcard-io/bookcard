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
