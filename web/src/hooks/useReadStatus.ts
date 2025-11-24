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
  getReadStatus,
  updateReadStatus as updateReadStatusService,
} from "@/services/readingService";
import type { ReadStatus } from "@/types/reading";

export interface UseReadStatusOptions {
  /** Book ID. */
  bookId: number;
  /** Whether to automatically fetch on mount. */
  enabled?: boolean;
}

export interface UseReadStatusResult {
  /** Read status data. */
  status: ReadStatus | null;
  /** Whether data is currently being fetched. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** Function to refetch status. */
  refetch: () => void;
  /** Function to mark book as read. */
  markAsRead: () => Promise<ReadStatus>;
  /** Function to mark book as unread. */
  markAsUnread: () => Promise<ReadStatus>;
  /** Whether an update is in progress. */
  isUpdating: boolean;
  /** Error message if update failed. */
  updateError: string | null;
}

/**
 * Custom hook for fetching and managing read status.
 *
 * Provides loading state, error handling, and update functionality.
 * Follows IOC pattern by accepting options and returning state/actions.
 *
 * Parameters
 * ----------
 * options : UseReadStatusOptions
 *     Hook options including book ID.
 *
 * Returns
 * -------
 * UseReadStatusResult
 *     Status data, loading state, and control functions.
 */
export function useReadStatus(
  options: UseReadStatusOptions,
): UseReadStatusResult {
  const { bookId, enabled = true } = options;
  const { activeLibrary, isLoading: isActiveLibraryLoading } =
    useActiveLibrary();
  const queryClient = useQueryClient();

  const queryKey = useMemo(() => ["read-status", bookId] as const, [bookId]);

  const hasActiveLibrary = activeLibrary !== null && !isActiveLibraryLoading;
  const queryEnabled = enabled && hasActiveLibrary && bookId > 0;

  const query = useQuery<ReadStatus, Error>({
    queryKey,
    queryFn: () => getReadStatus(bookId),
    enabled: queryEnabled,
    staleTime: 60_000, // 1 minute
  });

  const mutation = useMutation<ReadStatus, Error, "read" | "not_read">({
    mutationFn: (status) => updateReadStatusService(bookId, status),
    onSuccess: (data) => {
      // Update the query cache with the new status
      queryClient.setQueryData(queryKey, data);
      // Also invalidate related queries
      queryClient.invalidateQueries({ queryKey: ["read-status"] });
      queryClient.invalidateQueries({ queryKey: ["recent-reads"] });
    },
  });

  return {
    status: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error?.message ?? null,
    refetch: () => {
      void query.refetch();
    },
    markAsRead: async () => {
      return mutation.mutateAsync("read");
    },
    markAsUnread: async () => {
      return mutation.mutateAsync("not_read");
    },
    isUpdating: mutation.isPending,
    updateError: mutation.error?.message ?? null,
  };
}
