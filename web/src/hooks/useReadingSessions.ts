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

import type { InfiniteData } from "@tanstack/react-query";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import { listSessions } from "@/services/readingService";
import type { ReadingSessionsListResponse } from "@/types/reading";

export interface UseReadingSessionsOptions {
  /** Filter by book ID (optional). */
  bookId?: number;
  /** Page number (default: 1). */
  page?: number;
  /** Items per page (default: 50). */
  pageSize?: number;
  /** Whether to enable infinite scroll mode. */
  infiniteScroll?: boolean;
  /** Whether to automatically fetch on mount. */
  enabled?: boolean;
}

export interface UseReadingSessionsResult {
  /** List of reading sessions. */
  sessions: ReadingSessionsListResponse["sessions"];
  /** Total number of sessions. */
  total: number;
  /** Current page number. */
  page: number;
  /** Number of items per page. */
  pageSize: number;
  /** Whether data is currently being fetched. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** Function to refetch sessions. */
  refetch: () => void;
  /** Function to load next page (only available when infiniteScroll is enabled). */
  loadMore?: () => void;
  /** Whether there are more pages to load (only available when infiniteScroll is enabled). */
  hasMore?: boolean;
}

/**
 * Custom hook for fetching reading sessions.
 *
 * Provides pagination and loading state management.
 * Follows IOC pattern by accepting options and returning state/actions.
 *
 * Parameters
 * ----------
 * options : UseReadingSessionsOptions
 *     Query parameters and options.
 *
 * Returns
 * -------
 * UseReadingSessionsResult
 *     Sessions data, loading state, and control functions.
 */
export function useReadingSessions(
  options: UseReadingSessionsOptions = {},
): UseReadingSessionsResult {
  const {
    bookId,
    page: initialPage = 1,
    pageSize: initialPageSize = 50,
    infiniteScroll = false,
    enabled = true,
  } = options;

  const { activeLibrary, isLoading: isActiveLibraryLoading } =
    useActiveLibrary();

  const listQueryKey = useMemo(
    () =>
      [
        "reading-sessions",
        { bookId, page: initialPage, pageSize: initialPageSize },
      ] as const,
    [bookId, initialPage, initialPageSize],
  );

  const infiniteQueryKey = useMemo(
    () =>
      [
        "reading-sessions-infinite",
        { bookId, pageSize: initialPageSize },
      ] as const,
    [bookId, initialPageSize],
  );

  const hasActiveLibrary = activeLibrary !== null && !isActiveLibraryLoading;
  const listQueryEnabled = enabled && !infiniteScroll && hasActiveLibrary;
  const infiniteQueryEnabled = enabled && infiniteScroll && hasActiveLibrary;

  const listQuery = useQuery<ReadingSessionsListResponse, Error>({
    queryKey: listQueryKey,
    queryFn: () => listSessions(bookId, initialPage, initialPageSize),
    enabled: listQueryEnabled,
    staleTime: 60_000, // 1 minute
  });

  const infiniteQuery = useInfiniteQuery<
    ReadingSessionsListResponse,
    Error,
    InfiniteData<ReadingSessionsListResponse>,
    readonly unknown[],
    number
  >({
    queryKey: infiniteQueryKey,
    queryFn: ({ pageParam = 1 }) =>
      listSessions(bookId, pageParam as number, initialPageSize),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const currentPage = lastPage.page ?? 1;
      const totalPages = Math.ceil(lastPage.total / lastPage.page_size);
      return currentPage < totalPages ? currentPage + 1 : undefined;
    },
    enabled: infiniteQueryEnabled,
    staleTime: 60_000, // 1 minute
  });

  const listData = listQuery.data;
  const infiniteData = infiniteQuery.data;

  if (infiniteScroll && infiniteData) {
    const sessions = infiniteData.pages.flatMap((page) => page.sessions);
    const total = infiniteData.pages[0]?.total ?? 0;
    const lastPage = infiniteData.pages[infiniteData.pages.length - 1];
    const currentPage = lastPage?.page ?? 1;
    const totalPages = Math.ceil(
      total / (lastPage?.page_size ?? initialPageSize),
    );
    const hasMore = currentPage < totalPages;

    return {
      sessions,
      total,
      page: currentPage,
      pageSize: lastPage?.page_size ?? initialPageSize,
      isLoading: infiniteQuery.isLoading,
      error: infiniteQuery.error?.message ?? null,
      refetch: () => {
        void infiniteQuery.refetch();
      },
      loadMore: () => {
        if (hasMore && !infiniteQuery.isFetchingNextPage) {
          void infiniteQuery.fetchNextPage();
        }
      },
      hasMore,
    };
  }

  return {
    sessions: listData?.sessions ?? [],
    total: listData?.total ?? 0,
    page: listData?.page ?? initialPage,
    pageSize: listData?.page_size ?? initialPageSize,
    isLoading: listQuery.isLoading,
    error: listQuery.error?.message ?? null,
    refetch: () => {
      void listQuery.refetch();
    },
  };
}
