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

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import {
  getProgress,
  updateProgress as updateProgressService,
} from "@/services/readingService";
import type { ReadingProgress, ReadingProgressCreate } from "@/types/reading";

export interface UseReadingProgressOptions {
  /** Book ID. */
  bookId: number;
  /** Book format (EPUB, PDF, etc.). */
  format: string;
  /** Whether to automatically fetch on mount. */
  enabled?: boolean;
}

export interface UseReadingProgressResult {
  /** Reading progress data. */
  progress: ReadingProgress | null;
  /** Whether data is currently being fetched. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** Function to refetch progress. */
  refetch: () => void;
  /** Function to update progress. */
  updateProgress: (data: ReadingProgressCreate) => Promise<ReadingProgress>;
  /** Whether an update is in progress. */
  isUpdating: boolean;
  /** Error message if update failed. */
  updateError: string | null;
}

/**
 * Custom hook for fetching and managing reading progress.
 *
 * Provides loading state, error handling, and update functionality.
 * Follows IOC pattern by accepting options and returning state/actions.
 *
 * Parameters
 * ----------
 * options : UseReadingProgressOptions
 *     Hook options including book ID and format.
 *
 * Returns
 * -------
 * UseReadingProgressResult
 *     Progress data, loading state, and control functions.
 */
export function useReadingProgress(
  options: UseReadingProgressOptions,
): UseReadingProgressResult {
  const { bookId, format, enabled = true } = options;
  const { activeLibrary, isLoading: isActiveLibraryLoading } =
    useActiveLibrary();
  const queryClient = useQueryClient();

  const queryKey = useMemo(
    () => ["reading-progress", bookId, format] as const,
    [bookId, format],
  );

  const hasActiveLibrary = activeLibrary !== null && !isActiveLibraryLoading;
  const queryEnabled = enabled && hasActiveLibrary && bookId > 0 && !!format;

  const query = useQuery<ReadingProgress | null, Error>({
    queryKey,
    queryFn: () => getProgress(bookId, format),
    enabled: queryEnabled,
    staleTime: 30_000, // 30 seconds
    retry: (failureCount, error) => {
      // Don't retry on 404 (no progress exists yet)
      if (error?.message?.includes("404") || failureCount > 2) {
        return false;
      }
      return true;
    },
  });

  const mutation = useMutation<ReadingProgress, Error, ReadingProgressCreate>({
    mutationFn: updateProgressService,
    onSuccess: (data) => {
      // Update the query cache with the new progress
      queryClient.setQueryData(queryKey, data);
      // Also invalidate related queries
      queryClient.invalidateQueries({ queryKey: ["reading-progress"] });
      queryClient.invalidateQueries({ queryKey: ["recent-reads"] });
    },
  });

  return {
    progress: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error?.message ?? null,
    refetch: () => {
      void query.refetch();
    },
    updateProgress: async (data: ReadingProgressCreate) => {
      return mutation.mutateAsync(data);
    },
    isUpdating: mutation.isPending,
    updateError: mutation.error?.message ?? null,
  };
}
