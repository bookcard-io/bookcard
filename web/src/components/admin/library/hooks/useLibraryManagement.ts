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
import { generateLibraryName } from "@/utils/library";
import type { Library } from "../types";

export interface UseLibraryManagementOptions {
  /** Whether to automatically fetch libraries on mount. */
  enabled?: boolean;
  /** Callback when libraries are refreshed (for syncing with active library context). */
  onRefresh?: () => Promise<void> | void;
}

export interface UseLibraryManagementResult {
  /** List of libraries. */
  libraries: Library[];
  /** Whether libraries are currently being fetched. */
  isLoading: boolean;
  /** Whether any operation is in progress. */
  isBusy: boolean;
  /** Error message if operation failed. */
  error: string | null;
  /** ID of library currently being deleted. */
  deletingLibraryId: number | null;
  /** ID of library currently being scanned. */
  scanningLibraryId: number | null;
  /** Function to manually refresh libraries. */
  refresh: () => Promise<void>;
  /** Function to add a new library. */
  addLibrary: (path: string, name?: string) => Promise<void>;
  /** Function to toggle library activation state. */
  toggleLibrary: (library: Library) => Promise<void>;
  /** Function to delete a library. */
  deleteLibrary: (id: number) => Promise<void>;
  /** Function to initiate a library scan. */
  scanLibrary: (libraryId: number) => Promise<void>;
  /** Function to clear error state. */
  clearError: () => void;
}

/**
 * Custom hook for managing library CRUD operations.
 *
 * Handles fetching, adding, toggling, and deleting libraries.
 * Follows SRP by focusing solely on library management operations.
 * Uses IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UseLibraryManagementOptions
 *     Configuration including enabled flag and refresh callback.
 *
 * Returns
 * -------
 * UseLibraryManagementResult
 *     Library data, loading states, and operation functions.
 */
export function useLibraryManagement(
  options: UseLibraryManagementOptions = {},
): UseLibraryManagementResult {
  const { enabled = true, onRefresh } = options;

  const [libraries, setLibraries] = useState<Library[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deletingLibraryId, setDeletingLibraryId] = useState<number | null>(
    null,
  );
  const [scanningLibraryId, setScanningLibraryId] = useState<number | null>(
    null,
  );

  const fetchLibraries = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch("/api/admin/libraries", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to load libraries");
      }

      const data = (await response.json()) as Library[];
      setLibraries(data);
    } catch {
      setError("Failed to load libraries");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch("/api/admin/libraries", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to load libraries");
      }

      const data = (await response.json()) as Library[];
      setLibraries(data);
    } catch {
      setError("Failed to refresh libraries");
    }
  }, []);

  useEffect(() => {
    if (enabled) {
      void fetchLibraries();
    }
  }, [enabled, fetchLibraries]);

  const addLibrary = useCallback(
    async (path: string, name?: string) => {
      const trimmedPath = path.trim();
      if (!trimmedPath) {
        setError("Path is required");
        return;
      }

      const libraryName = generateLibraryName(libraries, name);
      // Auto-activate if this is the first library
      const isFirstLibrary = libraries.length === 0;

      setIsBusy(true);
      setError(null);
      try {
        const response = await fetch("/api/admin/libraries", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: libraryName,
            calibre_db_path: trimmedPath,
            calibre_db_file: "metadata.db",
            is_active: isFirstLibrary,
          }),
        });

        if (!response.ok) {
          const data = (await response.json()) as { detail?: string };
          throw new Error(data.detail || "Failed to add library");
        }

        await refresh();
        if (onRefresh) {
          await onRefresh();
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to add library");
        throw err;
      } finally {
        setIsBusy(false);
      }
    },
    [libraries, refresh, onRefresh],
  );

  const toggleLibrary = useCallback(
    async (library: Library) => {
      setError(null);
      try {
        if (library.is_active) {
          // Deactivate by setting is_active to false
          const response = await fetch(`/api/admin/libraries/${library.id}`, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              is_active: false,
            }),
          });

          if (!response.ok) {
            const data = (await response.json()) as { detail?: string };
            throw new Error(data.detail || "Failed to deactivate library");
          }
        } else {
          // Activate using the activate endpoint
          const response = await fetch(
            `/api/admin/libraries/${library.id}/activate`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
            },
          );

          if (!response.ok) {
            const data = (await response.json()) as { detail?: string };
            throw new Error(data.detail || "Failed to activate library");
          }
        }

        await refresh();
        if (onRefresh) {
          await onRefresh();
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to toggle library activation state",
        );
        throw err;
      }
    },
    [refresh, onRefresh],
  );

  const deleteLibrary = useCallback(
    async (id: number) => {
      setDeletingLibraryId(id);
      setIsBusy(true);
      setError(null);
      try {
        const response = await fetch(`/api/admin/libraries/${id}`, {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          const data = (await response.json()) as { detail?: string };
          throw new Error(data.detail || "Failed to delete library");
        }

        await refresh();
        if (onRefresh) {
          await onRefresh();
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to delete library",
        );
        throw err;
      } finally {
        setIsBusy(false);
        setDeletingLibraryId(null);
      }
    },
    [refresh, onRefresh],
  );

  const scanLibrary = useCallback(async (libraryId: number) => {
    setScanningLibraryId(libraryId);
    setError(null);
    try {
      const response = await fetch("/api/library-scanning/scan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          library_id: libraryId,
          data_source_config: {
            name: "openlibrary",
            kwargs: {},
          },
        }),
      });

      if (!response.ok) {
        const data = (await response.json()) as { detail?: string };
        throw new Error(data.detail || "Failed to start library scan");
      }

      // Note: The scan runs in the background, so we don't wait for completion
      // The task_id from the response can be used to track progress if needed
      await response.json();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to start library scan",
      );
      throw err;
    } finally {
      // Reset scanning state after a short delay to show the button was clicked
      setTimeout(() => {
        setScanningLibraryId(null);
      }, 1000);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    libraries,
    isLoading,
    isBusy,
    error,
    deletingLibraryId,
    scanningLibraryId,
    refresh,
    addLibrary,
    toggleLibrary,
    deleteLibrary,
    scanLibrary,
    clearError,
  };
}
