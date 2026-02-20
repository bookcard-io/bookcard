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
  useMemo,
  useState,
} from "react";
import { useUser } from "@/contexts/UserContext";
import type { UserLibrary } from "@/types/userLibrary";

export interface Library {
  id: number;
  name: string;
  calibre_db_path: string;
  calibre_db_file: string;
  calibre_uuid: string | null;
  use_split_library: boolean;
  split_library_dir: string | null;
  auto_reconnect: boolean;
  created_at: string;
  updated_at: string;
}

interface LibraryContextType {
  /** The user's active library (ingest target). */
  activeLibrary: Library | null;
  /** Whether the context is still loading. */
  isLoading: boolean;
  /** Re-fetch all library data. */
  refresh: () => Promise<void>;
  /** All visible libraries for the current user. */
  visibleLibraries: Library[];
  /** Currently selected library ID for filtering (null = "All"). */
  selectedLibraryId: number | null;
  /** Update the selected library filter. */
  setSelectedLibraryId: (id: number | null) => void;
}

const STORAGE_KEY = "bookcard:selectedLibraryId";

const LibraryContext = createContext<LibraryContextType | undefined>(undefined);

function readStoredLibraryId(): number | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === null) return null;
    const parsed = Number(stored);
    return Number.isFinite(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function writeStoredLibraryId(id: number | null): void {
  try {
    if (id === null) {
      localStorage.removeItem(STORAGE_KEY);
    } else {
      localStorage.setItem(STORAGE_KEY, String(id));
    }
  } catch {
    // localStorage unavailable (e.g. SSR, private browsing)
  }
}

export function ActiveLibraryProvider({ children }: { children: ReactNode }) {
  const { user, isLoading: userLoading } = useUser();
  const [activeLibrary, setActiveLibrary] = useState<Library | null>(null);
  const [visibleLibraries, setVisibleLibraries] = useState<Library[]>([]);
  const [selectedLibraryId, setSelectedLibraryIdState] = useState<
    number | null
  >(null);
  const [isLoading, setIsLoading] = useState(true);

  const setSelectedLibraryId = useCallback((id: number | null) => {
    setSelectedLibraryIdState(id);
    writeStoredLibraryId(id);
  }, []);

  const refresh = useCallback(async () => {
    // Wait for user context to finish loading
    if (userLoading) {
      return;
    }

    try {
      setIsLoading(true);

      // Always fetch the global active library (works for anonymous users too)
      const activeResponse = await fetch("/api/libraries/active");
      let resolvedActive: Library | null = null;
      if (activeResponse.ok) {
        resolvedActive = (await activeResponse.json()) as Library;
      }

      // If we have an authenticated user, fetch their library assignments
      let resolvedVisible: Library[] = [];
      if (user !== null) {
        try {
          const meResponse = await fetch("/api/libraries/me");
          if (meResponse.ok) {
            const assignments = (await meResponse.json()) as UserLibrary[];

            // Build visible libraries list from assignments
            const visible = assignments.filter((a) => a.is_visible);

            // Derive Library objects from assignments + the active library
            // We know library_name from the enriched endpoint
            resolvedVisible = visible.map((a) => ({
              // We have limited info from UserLibrary; use activeLibrary
              // details if it matches, otherwise create a minimal Library
              id: a.library_id,
              name: a.library_name ?? `Library ${a.library_id}`,
              // These fields are not available from the /me endpoint,
              // but they are not used for display purposes
              calibre_db_path: "",
              calibre_db_file: "",
              calibre_uuid: null,
              use_split_library: false,
              split_library_dir: null,
              auto_reconnect: false,
              created_at: a.created_at,
              updated_at: a.updated_at,
            }));

            // If there's an active assignment, use the full Library from
            // /api/libraries/active if IDs match (richer data)
            const activeAssignment = assignments.find((a) => a.is_active);
            if (
              activeAssignment &&
              resolvedActive &&
              resolvedActive.id === activeAssignment.library_id
            ) {
              // activeLibrary from /active has full data; use it
              // Also replace the matching entry in visibleLibraries
              const active = resolvedActive;
              resolvedVisible = resolvedVisible.map((lib) =>
                lib.id === active.id ? active : lib,
              );
            } else if (activeAssignment && !resolvedActive) {
              // Fallback: use the minimal library from assignments
              resolvedActive =
                resolvedVisible.find(
                  (lib) => lib.id === activeAssignment.library_id,
                ) ?? null;
            }
          }
        } catch {
          // If /me fails (e.g. no assignments yet), fall back gracefully
        }
      }

      setActiveLibrary(resolvedActive);
      setVisibleLibraries(resolvedVisible);

      // Restore selectedLibraryId from localStorage and validate it
      const storedId = readStoredLibraryId();
      if (resolvedVisible.length <= 1) {
        // Single library or none: select it directly (no "All" needed)
        const singleId =
          resolvedVisible.length === 1
            ? (resolvedVisible[0]?.id ?? null)
            : null;
        setSelectedLibraryIdState(singleId);
        writeStoredLibraryId(singleId);
      } else if (
        storedId !== null &&
        resolvedVisible.some((lib) => lib.id === storedId)
      ) {
        // Stored ID is valid
        setSelectedLibraryIdState(storedId);
      } else {
        // Default to "All" for multi-library users
        setSelectedLibraryIdState(null);
        writeStoredLibraryId(null);
      }
    } catch {
      setActiveLibrary(null);
      setVisibleLibraries([]);
    } finally {
      setIsLoading(false);
    }
  }, [userLoading, user]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const value = useMemo<LibraryContextType>(
    () => ({
      activeLibrary,
      isLoading,
      refresh,
      visibleLibraries,
      selectedLibraryId,
      setSelectedLibraryId,
    }),
    [
      activeLibrary,
      isLoading,
      refresh,
      visibleLibraries,
      selectedLibraryId,
      setSelectedLibraryId,
    ],
  );

  return (
    <LibraryContext.Provider value={value}>{children}</LibraryContext.Provider>
  );
}

/**
 * Hook to access library context.
 *
 * Provides the active library, visible libraries, and the selected
 * library filter for the sidebar.
 */
export function useActiveLibrary() {
  const context = useContext(LibraryContext);
  if (context === undefined) {
    throw new Error(
      "useActiveLibrary must be used within an ActiveLibraryProvider",
    );
  }
  return context;
}

// Alias for more descriptive naming in new code
export { useActiveLibrary as useLibrary };
export { ActiveLibraryProvider as LibraryProvider };
