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
 * Hook for managing shelves.
 *
 * Provides functionality to list, create, update, and delete shelves.
 */

import { useCallback, useEffect, useState } from "react";
import {
  type CreateShelfOptions,
  createShelf,
  deleteShelf as deleteShelfApi,
  listShelves,
  updateShelf as updateShelfApi,
} from "@/services/shelfService";
import type { Shelf, ShelfCreate, ShelfUpdate } from "@/types/shelf";

interface UseShelvesReturn {
  /** List of shelves. */
  shelves: Shelf[];
  /** Whether shelves are currently loading. */
  isLoading: boolean;
  /** Error message if any. */
  error: string | null;
  /** Create a new shelf. */
  createShelf: (
    data: ShelfCreate,
    options?: CreateShelfOptions,
  ) => Promise<Shelf>;
  /** Update an existing shelf. */
  updateShelf: (id: number, data: ShelfUpdate) => Promise<Shelf>;
  /** Delete a shelf. */
  deleteShelf: (id: number) => Promise<void>;
  /** Refresh the shelves list. */
  refresh: () => Promise<void>;
}

/**
 * Hook for managing shelves.
 *
 * Returns
 * -------
 * UseShelvesReturn
 *     Object with shelves list, loading state, and CRUD operations.
 */
export function useShelves(): UseShelvesReturn {
  const [shelves, setShelves] = useState<Shelf[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadShelves = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await listShelves();
      setShelves(response.shelves);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load shelves");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadShelves();
  }, [loadShelves]);

  const handleCreateShelf = useCallback(
    async (data: ShelfCreate, options?: CreateShelfOptions): Promise<Shelf> => {
      setError(null);
      try {
        const newShelf = await createShelf(data, options);
        await loadShelves();
        return newShelf;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to create shelf";
        setError(errorMessage);
        throw err;
      }
    },
    [loadShelves],
  );

  const handleUpdateShelf = useCallback(
    async (id: number, data: ShelfUpdate): Promise<Shelf> => {
      setError(null);
      try {
        const updatedShelf = await updateShelfApi(id, data);
        await loadShelves();
        return updatedShelf;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to update shelf";
        setError(errorMessage);
        throw err;
      }
    },
    [loadShelves],
  );

  const handleDeleteShelf = useCallback(
    async (id: number): Promise<void> => {
      setError(null);
      try {
        await deleteShelfApi(id);
        await loadShelves();
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to delete shelf";
        setError(errorMessage);
        throw err;
      }
    },
    [loadShelves],
  );

  return {
    shelves,
    isLoading,
    error,
    createShelf: handleCreateShelf,
    updateShelf: handleUpdateShelf,
    deleteShelf: handleDeleteShelf,
    refresh: loadShelves,
  };
}
