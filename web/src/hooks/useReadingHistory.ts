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

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import { getReadingHistory } from "@/services/readingService";
import type { ReadingHistoryResponse } from "@/types/reading";

export interface UseReadingHistoryOptions {
  /** Book ID. */
  bookId: number;
  /** Maximum number of sessions (default: 50). */
  limit?: number;
  /** Whether to automatically fetch on mount. */
  enabled?: boolean;
}

export interface UseReadingHistoryResult {
  /** List of reading sessions. */
  sessions: ReadingHistoryResponse["sessions"];
  /** Total number of sessions. */
  total: number;
  /** Whether data is currently being fetched. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** Function to refetch reading history. */
  refetch: () => void;
}

/**
 * Custom hook for fetching reading history for a book.
 *
 * Provides loading state and error handling.
 * Follows IOC pattern by accepting options and returning state/actions.
 *
 * Parameters
 * ----------
 * options : UseReadingHistoryOptions
 *     Query parameters and options.
 *
 * Returns
 * -------
 * UseReadingHistoryResult
 *     Reading history data, loading state, and control functions.
 */
export function useReadingHistory(
  options: UseReadingHistoryOptions,
): UseReadingHistoryResult {
  const { bookId, limit = 50, enabled = true } = options;
  const { activeLibrary, isLoading: isActiveLibraryLoading } =
    useActiveLibrary();

  const queryKey = useMemo(
    () => ["reading-history", bookId, { limit }] as const,
    [bookId, limit],
  );

  const hasActiveLibrary = activeLibrary !== null && !isActiveLibraryLoading;
  const queryEnabled = enabled && hasActiveLibrary && bookId > 0;

  const query = useQuery<ReadingHistoryResponse, Error>({
    queryKey,
    queryFn: () => getReadingHistory(bookId, limit),
    enabled: queryEnabled,
    staleTime: 60_000, // 1 minute
  });

  return {
    sessions: query.data?.sessions ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error?.message ?? null,
    refetch: () => {
      void query.refetch();
    },
  };
}
