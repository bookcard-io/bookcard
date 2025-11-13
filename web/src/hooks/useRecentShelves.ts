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

import { useCallback, useEffect, useState } from "react";
import type { Shelf } from "@/types/shelf";

/** LocalStorage key for storing recent shelves. */
const RECENT_SHELVES_KEY = "calibre_recent_shelves";

/** Maximum number of recent shelves to track. */
const MAX_RECENT_SHELVES = 5;

interface UseRecentShelvesReturn {
  /** List of recent shelf IDs (most recent first). */
  recentShelfIds: number[];
  /** Add a shelf to recent list. */
  addRecentShelf: (shelfId: number) => void;
  /** Get recent shelves from available shelves. */
  getRecentShelves: (allShelves: Shelf[]) => Shelf[];
}

/**
 * Hook for managing recent shelves.
 *
 * Tracks recently used shelves in localStorage and provides methods
 * to add shelves and retrieve recent shelves from a full list.
 * Follows SRP by managing only recent shelves tracking.
 * Follows IOC by accepting shelves list as input.
 *
 * Returns
 * -------
 * UseRecentShelvesReturn
 *     Recent shelf IDs, add function, and get recent shelves function.
 */
export function useRecentShelves(): UseRecentShelvesReturn {
  const [recentShelfIds, setRecentShelfIds] = useState<number[]>([]);

  // Load recent shelves from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(RECENT_SHELVES_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as number[];
        if (Array.isArray(parsed)) {
          setRecentShelfIds(parsed);
        }
      }
    } catch {
      // Ignore parse errors, use empty array
    }
  }, []);

  /**
   * Add a shelf to recent list.
   *
   * Parameters
   * ----------
   * shelfId : number
   *     Shelf ID to add to recent list.
   */
  const addRecentShelf = useCallback((shelfId: number) => {
    setRecentShelfIds((prev) => {
      // Remove if already exists, then add to front
      const filtered = prev.filter((id) => id !== shelfId);
      const updated = [shelfId, ...filtered].slice(0, MAX_RECENT_SHELVES);

      // Persist to localStorage
      try {
        localStorage.setItem(RECENT_SHELVES_KEY, JSON.stringify(updated));
      } catch {
        // Ignore storage errors
      }

      return updated;
    });
  }, []);

  /**
   * Get recent shelves from available shelves.
   *
   * Parameters
   * ----------
   * allShelves : Shelf[]
   *     Full list of available shelves.
   *
   * Returns
   * -------
   * Shelf[]
   *     Recent shelves in order (most recent first).
   */
  const getRecentShelves = useCallback(
    (allShelves: Shelf[]): Shelf[] => {
      const shelfMap = new Map(allShelves.map((s) => [s.id, s]));
      return recentShelfIds
        .map((id) => shelfMap.get(id))
        .filter((shelf): shelf is Shelf => shelf !== undefined);
    },
    [recentShelfIds],
  );

  return {
    recentShelfIds,
    addRecentShelf,
    getRecentShelves,
  };
}
