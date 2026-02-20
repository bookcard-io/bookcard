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

import { useCallback, useEffect, useRef, useState } from "react";
import type { UserLibrary } from "@/types/userLibrary";

interface LibrarySummary {
  id: number;
  name: string;
}

export interface UseUserLibraryManagementReturn {
  /** Current library assignments for the user. */
  assignments: UserLibrary[];
  /** All libraries available in the system (for the assign dropdown). */
  allLibraries: LibrarySummary[];
  /** Whether data is still loading. */
  isLoading: boolean;
  /** Whether a mutation is in progress. */
  isBusy: boolean;
  /** Error message, if any. */
  error: string | null;
  /** Assign a library to the user. */
  assignLibrary: (libraryId: number) => Promise<void>;
  /** Unassign a library from the user. */
  unassignLibrary: (libraryId: number) => Promise<void>;
  /** Set a library as the user's active (ingest) library. */
  setActiveLibrary: (libraryId: number) => Promise<void>;
  /** Toggle visibility for a library. */
  toggleVisibility: (libraryId: number, isVisible: boolean) => Promise<void>;
  /** Clear the current error. */
  clearError: () => void;
}

/**
 * Hook for managing a user's library assignments (admin).
 *
 * Fetches the user's current assignments and all available libraries,
 * then provides CRUD operations that hit the admin API endpoints.
 * Follows SRP by focusing solely on user-library association management.
 *
 * Parameters
 * ----------
 * userId : number | null
 *     User ID to manage. When null, the hook is inactive.
 *
 * Returns
 * -------
 * UseUserLibraryManagementReturn
 *     Assignments, available libraries, loading/error state, and mutation functions.
 */
export function useUserLibraryManagement(
  userId: number | null,
): UseUserLibraryManagementReturn {
  const [assignments, setAssignments] = useState<UserLibrary[]>([]);
  const [allLibraries, setAllLibraries] = useState<LibrarySummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const fetchData = useCallback(async () => {
    if (userId === null) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setIsLoading(true);
    setError(null);

    try {
      const [assignmentsRes, librariesRes] = await Promise.all([
        fetch(`/api/admin/users/${userId}/libraries`, {
          signal: controller.signal,
        }),
        fetch("/api/admin/libraries", { signal: controller.signal }),
      ]);

      if (controller.signal.aborted) return;

      if (!assignmentsRes.ok) {
        throw new Error("Failed to fetch user library assignments");
      }
      if (!librariesRes.ok) {
        throw new Error("Failed to fetch libraries");
      }

      const assignmentsData = (await assignmentsRes.json()) as UserLibrary[];
      const librariesData = (await librariesRes.json()) as Array<{
        id: number;
        name: string;
      }>;

      if (controller.signal.aborted) return;

      setAssignments(assignmentsData);
      setAllLibraries(
        librariesData.map((lib) => ({ id: lib.id, name: lib.name })),
      );
    } catch (err) {
      if (controller.signal.aborted) return;
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      if (!controller.signal.aborted) {
        setIsLoading(false);
      }
    }
  }, [userId]);

  useEffect(() => {
    void fetchData();
    return () => abortRef.current?.abort();
  }, [fetchData]);

  const assignLibrary = useCallback(
    async (libraryId: number) => {
      if (userId === null) return;
      setIsBusy(true);
      setError(null);
      try {
        const res = await fetch(`/api/admin/users/${userId}/libraries`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            library_id: libraryId,
            is_visible: true,
            is_active: false,
          }),
        });
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || "Failed to assign library");
        }
        await fetchData();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setIsBusy(false);
      }
    },
    [userId, fetchData],
  );

  const unassignLibrary = useCallback(
    async (libraryId: number) => {
      if (userId === null) return;
      setIsBusy(true);
      setError(null);
      try {
        const res = await fetch(
          `/api/admin/users/${userId}/libraries/${libraryId}`,
          { method: "DELETE" },
        );
        if (!res.ok && res.status !== 204) {
          const data = await res.json();
          throw new Error(data.detail || "Failed to unassign library");
        }
        setAssignments((prev) =>
          prev.filter((a) => a.library_id !== libraryId),
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setIsBusy(false);
      }
    },
    [userId],
  );

  const setActiveLibrary = useCallback(
    async (libraryId: number) => {
      if (userId === null) return;
      setIsBusy(true);
      setError(null);
      try {
        const res = await fetch(
          `/api/admin/users/${userId}/libraries/${libraryId}/active`,
          { method: "PUT", headers: { "Content-Type": "application/json" } },
        );
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || "Failed to set active library");
        }
        setAssignments((prev) =>
          prev.map((a) => ({ ...a, is_active: a.library_id === libraryId })),
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setIsBusy(false);
      }
    },
    [userId],
  );

  const toggleVisibility = useCallback(
    async (libraryId: number, isVisible: boolean) => {
      if (userId === null) return;
      setIsBusy(true);
      setError(null);
      try {
        const res = await fetch(
          `/api/admin/users/${userId}/libraries/${libraryId}/visibility`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_visible: isVisible }),
          },
        );
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || "Failed to update visibility");
        }
        setAssignments((prev) =>
          prev.map((a) =>
            a.library_id === libraryId ? { ...a, is_visible: isVisible } : a,
          ),
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setIsBusy(false);
      }
    },
    [userId],
  );

  return {
    assignments,
    allLibraries,
    isLoading,
    isBusy,
    error,
    assignLibrary,
    unassignLibrary,
    setActiveLibrary,
    toggleVisibility,
    clearError,
  };
}
