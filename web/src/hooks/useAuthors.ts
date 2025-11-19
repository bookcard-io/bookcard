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

import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import { fetchAuthorsPage } from "@/services/authorService";
import type { AuthorListResponse, AuthorWithMetadata } from "@/types/author";

export interface UseAuthorsOptions {
  /** Whether to automatically fetch on mount. */
  enabled?: boolean;
  /** Whether to enable infinite scroll mode (accumulates authors across pages). */
  infiniteScroll?: boolean;
  /** Number of items per page. */
  pageSize?: number;
}

export interface UseAuthorsResult {
  /** List of authors (accumulated if infinite scroll is enabled). */
  authors: AuthorWithMetadata[];
  /** Total number of authors. */
  total: number;
  /** Whether data is currently being fetched. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** Function to load next page (only available when infiniteScroll is enabled). */
  loadMore?: () => void;
  /** Whether there are more pages to load (only available when infiniteScroll is enabled). */
  hasMore?: boolean;
}

/**
 * Custom hook for fetching and managing authors data.
 *
 * Provides pagination and loading state management using react-query.
 * Follows IOC pattern by accepting options and returning state/actions.
 *
 * Parameters
 * ----------
 * options : UseAuthorsOptions
 *     Query parameters and options.
 *
 * Returns
 * -------
 * UseAuthorsResult
 *     Authors data, loading state, and control functions.
 */
export function useAuthors(options: UseAuthorsOptions = {}): UseAuthorsResult {
  const { enabled = true, infiniteScroll = false, pageSize = 20 } = options;

  const { activeLibrary, isLoading: isActiveLibraryLoading } =
    useActiveLibrary();

  const listQueryKey = useMemo(
    () => ["authors", { pageSize }] as const,
    [pageSize],
  );

  const infiniteQueryKey = useMemo(
    () => ["authors-infinite", { pageSize }] as const,
    [pageSize],
  );

  // Only enable queries if there's an active library and not still loading
  const hasActiveLibrary = activeLibrary !== null && !isActiveLibraryLoading;
  const queryEnabled = enabled && hasActiveLibrary;

  const listQuery = useQuery<AuthorListResponse, Error>({
    queryKey: listQueryKey,
    queryFn: () =>
      fetchAuthorsPage({
        page: 1,
        pageSize,
      }),
    enabled: queryEnabled && !infiniteScroll,
    staleTime: 60_000,
  });

  const infiniteQuery = useInfiniteQuery<AuthorListResponse, Error>({
    queryKey: infiniteQueryKey,
    queryFn: ({ pageParam }) =>
      fetchAuthorsPage({
        page: (pageParam as number | undefined) ?? 1,
        pageSize,
      }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const currentPage = lastPage.page ?? 1;
      const totalPages = lastPage.total_pages ?? 0;
      return currentPage < totalPages ? currentPage + 1 : undefined;
    },
    enabled: queryEnabled && infiniteScroll,
    staleTime: 60_000,
  });

  const data = listQuery.data;
  const infiniteData = infiniteQuery.data;

  const authors: AuthorWithMetadata[] = useMemo(() => {
    if (infiniteScroll) {
      if (!infiniteData) return [];
      const allItems = infiniteData.pages.flatMap(
        (pageData) => pageData?.items ?? [],
      );
      // Deduplicate by key or name
      const seen = new Set<string>();
      return allItems.filter((author) => {
        const id = author.key || author.name;
        if (seen.has(id)) return false;
        seen.add(id);
        return true;
      });
    }
    return data?.items ?? [];
  }, [infiniteScroll, infiniteData, data]);

  const total = useMemo(() => {
    if (infiniteScroll) {
      const firstPage = infiniteData?.pages[0];
      return firstPage ? firstPage.total : 0;
    }
    return data?.total ?? 0;
  }, [infiniteScroll, infiniteData, data]);

  const isLoading =
    isActiveLibraryLoading ||
    (infiniteScroll
      ? infiniteQuery.isPending || infiniteQuery.isFetching
      : listQuery.isPending || listQuery.isFetching);

  // Show friendly error if no active library, otherwise show API error
  const error =
    !isActiveLibraryLoading && !hasActiveLibrary
      ? "no_active_library"
      : (infiniteScroll && infiniteQuery.error?.message) ||
        listQuery.error?.message ||
        null;

  const loadMore = useCallback(() => {
    if (!infiniteScroll) {
      return;
    }
    if (!infiniteQuery.hasNextPage) {
      return;
    }
    void infiniteQuery.fetchNextPage();
  }, [infiniteScroll, infiniteQuery]);

  const hasMore = !!(infiniteScroll && infiniteQuery.hasNextPage);

  return {
    authors,
    total,
    isLoading,
    error,
    loadMore,
    hasMore,
  };
}
