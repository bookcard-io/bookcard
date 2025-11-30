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

"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { listShelves } from "@/services/shelfService";
import type { Shelf } from "@/types/shelf";
import { useActiveLibrary } from "./ActiveLibraryContext";

interface ShelvesContextType {
  /** List of active shelves for the active library. */
  shelves: Shelf[];
  /** Whether shelves are currently loading. */
  isLoading: boolean;
  /** Error message if any. */
  error: string | null;
  /** Refresh the shelves list. */
  refresh: () => Promise<void>;
}

const ShelvesContext = createContext<ShelvesContextType | undefined>(undefined);

/**
 * Provider for shelves context.
 *
 * Manages shelves data for the active library. Only loads shelves when
 * an active library is available. Follows SRP by managing only shelves
 * data fetching concerns. Follows IOC by depending on ActiveLibraryContext.
 */
export function ShelvesProvider({ children }: { children: ReactNode }) {
  const { activeLibrary } = useActiveLibrary();
  const [shelves, setShelves] = useState<Shelf[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Extract library ID to avoid unnecessary refreshes when only library object reference changes
  const activeLibraryId = activeLibrary?.id ?? null;

  const refresh = useCallback(async () => {
    // Only load shelves if there's an active library
    if (!activeLibraryId) {
      setShelves([]);
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const response = await listShelves();
      // Filter to only active shelves for the active library
      const activeShelves = response.shelves.filter(
        (shelf) => shelf.is_active && shelf.library_id === activeLibraryId,
      );
      setShelves(activeShelves);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load shelves");
      setShelves([]);
    } finally {
      setIsLoading(false);
    }
  }, [activeLibraryId]); // Only depend on library ID, not the whole object

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <ShelvesContext.Provider value={{ shelves, isLoading, error, refresh }}>
      {children}
    </ShelvesContext.Provider>
  );
}

/**
 * Hook to access shelves context.
 *
 * Returns
 * -------
 * ShelvesContextType
 *     Shelves data, loading state, error, and refresh function.
 *
 * Raises
 * ------
 * Error
 *     If used outside of ShelvesProvider.
 */
export function useShelvesContext() {
  const context = useContext(ShelvesContext);
  if (context === undefined) {
    throw new Error("useShelvesContext must be used within a ShelvesProvider");
  }
  return context;
}
