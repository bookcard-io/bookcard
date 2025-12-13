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

import type { InfiniteData, QueryClient } from "@tanstack/react-query";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import {
  getReadStatus,
  updateReadStatus as updateReadStatusService,
} from "@/services/readingService";
import type { BookListResponse, BookReadingSummary } from "@/types/book";
import type { ReadStatus, ReadStatusValue } from "@/types/reading";
import {
  bookInfiniteQueryKeys,
  bookListQueryKeys,
  readStatusBaseQueryKey,
  readStatusQueryKey,
  recentReadsQueryKey,
} from "@/utils/queryKeys";

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

interface OptimisticUpdateContext {
  /** Previous per-book read-status query value (if any). */
  previousReadStatus: ReadStatus | null | undefined;
  /** Snapshots of list-like queries that embed `reading_summary` denormalized data. */
  previousBooks: Array<[readonly unknown[], BookListResponse | undefined]>;
  previousBooksInfinite: Array<
    [readonly unknown[], InfiniteData<BookListResponse> | undefined]
  >;
  previousFilteredBooks: Array<
    [readonly unknown[], BookListResponse | undefined]
  >;
  previousFilteredBooksInfinite: Array<
    [readonly unknown[], InfiniteData<BookListResponse> | undefined]
  >;
}

/**
 * Create a patch function for updating reading summary in book objects.
 *
 * Parameters
 * ----------
 * newStatus : ReadStatusValue | null
 *     New read status value to apply.
 *
 * Returns
 * -------
 * (summary: BookReadingSummary | null | undefined) => BookReadingSummary
 *     Function that patches a reading summary with the new status.
 */
function createReadingSummaryPatch(
  newStatus: ReadStatusValue | null,
): (summary: BookReadingSummary | null | undefined) => BookReadingSummary {
  return (summary: BookReadingSummary | null | undefined) => {
    const base: BookReadingSummary = summary ?? {
      read_status: null,
      max_progress: null,
    };
    return {
      ...base,
      read_status: newStatus,
    };
  };
}

/**
 * Patch a book list response with updated reading summary for a specific book.
 *
 * Parameters
 * ----------
 * prev : BookListResponse | undefined
 *     Previous book list response.
 * bookId : number
 *     Book ID to update.
 * patch : (summary: BookReadingSummary | null | undefined) => BookReadingSummary
 *     Function to patch the reading summary.
 *
 * Returns
 * -------
 * BookListResponse | undefined
 *     Updated book list response or undefined if prev was undefined.
 */
function patchBookList(
  prev: BookListResponse | undefined,
  bookId: number,
  patch: (summary: BookReadingSummary | null | undefined) => BookReadingSummary,
): BookListResponse | undefined {
  if (!prev) return prev;
  return {
    ...prev,
    items: prev.items.map((b) =>
      b.id === bookId ? { ...b, reading_summary: patch(b.reading_summary) } : b,
    ),
  };
}

/**
 * Patch an infinite book list response with updated reading summary for a specific book.
 *
 * Parameters
 * ----------
 * prev : InfiniteData<BookListResponse> | undefined
 *     Previous infinite book list response.
 * bookId : number
 *     Book ID to update.
 * patch : (summary: BookReadingSummary | null | undefined) => BookReadingSummary
 *     Function to patch the reading summary.
 *
 * Returns
 * -------
 * InfiniteData<BookListResponse> | undefined
 *     Updated infinite book list response or undefined if prev was undefined.
 */
function patchInfiniteBookList(
  prev: InfiniteData<BookListResponse> | undefined,
  bookId: number,
  patch: (summary: BookReadingSummary | null | undefined) => BookReadingSummary,
): InfiniteData<BookListResponse> | undefined {
  if (!prev) return prev;
  return {
    ...prev,
    pages: prev.pages.map(
      (page) => patchBookList(page, bookId, patch) as BookListResponse,
    ),
  };
}

/**
 * Snapshot book list caches for optimistic update rollback.
 *
 * Parameters
 * ----------
 * queryClient : QueryClient
 *     React Query client instance.
 *
 * Returns
 * -------
 * Omit<OptimisticUpdateContext, 'previousReadStatus'>
 *     Context containing snapshots of all book list caches.
 */
function snapshotBookCaches(
  queryClient: QueryClient,
): Omit<OptimisticUpdateContext, "previousReadStatus"> {
  return {
    previousBooks: queryClient.getQueriesData<BookListResponse>({
      queryKey: [bookListQueryKeys[0]],
    }),
    previousBooksInfinite: queryClient.getQueriesData<
      InfiniteData<BookListResponse>
    >({
      queryKey: [bookInfiniteQueryKeys[0]],
    }),
    previousFilteredBooks: queryClient.getQueriesData<BookListResponse>({
      queryKey: [bookListQueryKeys[1]],
    }),
    previousFilteredBooksInfinite: queryClient.getQueriesData<
      InfiniteData<BookListResponse>
    >({
      queryKey: [bookInfiniteQueryKeys[1]],
    }),
  };
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

  const queryKey = useMemo(() => readStatusQueryKey(bookId), [bookId]);

  const hasActiveLibrary = activeLibrary !== null && !isActiveLibraryLoading;
  const queryEnabled = enabled && hasActiveLibrary && bookId > 0;

  const query = useQuery<ReadStatus | null, Error>({
    queryKey,
    queryFn: () => getReadStatus(bookId),
    enabled: queryEnabled,
    staleTime: 60_000, // 1 minute
    retry: (failureCount, error) => {
      // Don't retry on 404 errors (book not read is a valid state)
      // Only retry on network errors or other server errors
      if (error?.message?.includes("read_status_not_found")) {
        return false;
      }
      // Default retry behavior for other errors (max 3 retries)
      return failureCount < 3;
    },
  });

  // Update book list caches with new read status
  const updateCachedSummaries = useCallback(
    (newStatus: ReadStatusValue | null) => {
      const patch = createReadingSummaryPatch(newStatus);

      // Update all list queries
      bookListQueryKeys.forEach((key) => {
        queryClient.setQueriesData<BookListResponse>(
          { queryKey: [key] },
          (prev) => patchBookList(prev, bookId, patch),
        );
      });

      // Update all infinite list queries
      bookInfiniteQueryKeys.forEach((key) => {
        queryClient.setQueriesData<InfiniteData<BookListResponse>>(
          { queryKey: [key] },
          (prev) => patchInfiniteBookList(prev, bookId, patch),
        );
      });
    },
    [bookId, queryClient],
  );

  const mutation = useMutation<
    ReadStatus,
    Error,
    "read" | "not_read",
    OptimisticUpdateContext
  >({
    mutationFn: (status) => updateReadStatusService(bookId, status),
    onMutate: (status) => {
      // Snapshot state for rollback
      const cacheSnapshot = snapshotBookCaches(queryClient);
      const ctx: OptimisticUpdateContext = {
        previousReadStatus: queryClient.getQueryData(queryKey),
        ...cacheSnapshot,
      };

      // Optimistic update: immediately update book list caches
      const nextStatus: ReadStatusValue =
        status === "read" ? "read" : "not_read";
      updateCachedSummaries(nextStatus);

      // Optimistically update the per-book read-status cache if it already exists.
      // If the cache is empty, we rely on denormalized `reading_summary` updates.
      queryClient.setQueryData<ReadStatus | null>(queryKey, (prev) => {
        if (!prev) {
          return prev ?? null;
        }
        return {
          ...prev,
          status: nextStatus,
        };
      });

      return ctx;
    },
    onSuccess: (data) => {
      // Update the query cache with the new status
      queryClient.setQueryData(queryKey, data);
      // Invalidate related queries to ensure eventual consistency
      // Note: We skip manual cache updates here since onSettled will invalidate
      // book list queries, avoiding redundant work and race conditions.
      queryClient.invalidateQueries({ queryKey: readStatusBaseQueryKey });
      queryClient.invalidateQueries({ queryKey: recentReadsQueryKey });
    },
    onError: (_error, _variables, context) => {
      // Roll back optimistic updates.
      if (!context) {
        return;
      }

      queryClient.setQueryData(queryKey, context.previousReadStatus ?? null);

      for (const [key, data] of context.previousBooks) {
        queryClient.setQueryData(key, data);
      }
      for (const [key, data] of context.previousBooksInfinite) {
        queryClient.setQueryData(key, data);
      }
      for (const [key, data] of context.previousFilteredBooks) {
        queryClient.setQueryData(key, data);
      }
      for (const [key, data] of context.previousFilteredBooksInfinite) {
        queryClient.setQueryData(key, data);
      }
    },
    onSettled: () => {
      // Invalidate book list queries to ensure eventual consistency
      bookListQueryKeys.forEach((key) => {
        queryClient.invalidateQueries({ queryKey: [key] });
      });
      bookInfiniteQueryKeys.forEach((key) => {
        queryClient.invalidateQueries({ queryKey: [key] });
      });
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
