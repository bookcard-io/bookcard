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
 * Hook for managing a single shelf.
 *
 * Provides functionality to get shelf details and manage shelf state.
 */

import { useCallback, useEffect, useState } from "react";
import { getShelf } from "@/services/shelfService";
import type { Shelf } from "@/types/shelf";

interface UseShelfReturn {
  /** Shelf data. */
  shelf: Shelf | null;
  /** Whether shelf is currently loading. */
  isLoading: boolean;
  /** Error message if any. */
  error: string | null;
  /** Refresh the shelf data. */
  refresh: () => Promise<void>;
}

/**
 * Hook for managing a single shelf.
 *
 * Parameters
 * ----------
 * shelfId : number
 *     Shelf ID to load.
 *
 * Returns
 * -------
 * UseShelfReturn
 *     Object with shelf data, loading state, and refresh function.
 */
export function useShelf(shelfId: number): UseShelfReturn {
  const [shelf, setShelf] = useState<Shelf | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadShelf = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const shelfData = await getShelf(shelfId);
      setShelf(shelfData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load shelf");
    } finally {
      setIsLoading(false);
    }
  }, [shelfId]);

  useEffect(() => {
    void loadShelf();
  }, [loadShelf]);

  return {
    shelf,
    isLoading,
    error,
    refresh: loadShelf,
  };
}
