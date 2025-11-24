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
import { getRecentReads } from "@/services/readingService";
import type { RecentReadsResponse } from "@/types/reading";

export interface UseRecentReadsOptions {
  /** Maximum number of recent reads (default: 10). */
  limit?: number;
  /** Whether to automatically fetch on mount. */
  enabled?: boolean;
}

export interface UseRecentReadsResult {
  /** List of recent reads. */
  reads: RecentReadsResponse["reads"];
  /** Total number of recent reads. */
  total: number;
  /** Whether data is currently being fetched. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** Function to refetch recent reads. */
  refetch: () => void;
}

/**
 * Custom hook for fetching recent reads.
 *
 * Provides loading state and error handling.
 * Follows IOC pattern by accepting options and returning state/actions.
 *
 * Parameters
 * ----------
 * options : UseRecentReadsOptions
 *     Query parameters and options.
 *
 * Returns
 * -------
 * UseRecentReadsResult
 *     Recent reads data, loading state, and control functions.
 */
export function useRecentReads(
  options: UseRecentReadsOptions = {},
): UseRecentReadsResult {
  const { limit = 10, enabled = true } = options;
  const { activeLibrary, isLoading: isActiveLibraryLoading } =
    useActiveLibrary();

  const queryKey = useMemo(() => ["recent-reads", { limit }] as const, [limit]);

  const hasActiveLibrary = activeLibrary !== null && !isActiveLibraryLoading;
  const queryEnabled = enabled && hasActiveLibrary;

  const query = useQuery<RecentReadsResponse, Error>({
    queryKey,
    queryFn: () => getRecentReads(limit),
    enabled: queryEnabled,
    staleTime: 60_000, // 1 minute
  });

  return {
    reads: query.data?.reads ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error?.message ?? null,
    refetch: () => {
      void query.refetch();
    },
  };
}
