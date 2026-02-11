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
import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import type { SortField, SortOrder } from "@/constants/librarySorting";
import {
  DEFAULT_SORT_FIELD,
  DEFAULT_SORT_ORDER,
} from "@/constants/librarySorting";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import { useShelvesContext } from "@/contexts/ShelvesContext";
import { getShelfBooks } from "@/services/shelfService";
import type { Book, BookListResponse } from "@/types/book";
import type { ShelfBookRef } from "@/types/shelf";
import { deduplicateFetch, generateFetchKey } from "@/utils/fetch";
import { createEmptyFilters, filtersToApiBody } from "@/utils/filters";

export interface UseShelfBooksViewOptions {
  /** Shelf ID to load books for. */
  shelfId?: number;
  /** Number of items per page for shelf pagination. */
  pageSize?: number;
  /** Whether to fetch full book details with all metadata. */
  full?: boolean;
  /** Shelf ordering field (API: order, date_added, book_id, random). */
  shelfSortBy?: string;
  /** Shelf ordering direction (API: asc, desc). */
  shelfSortOrder?: string;
  /** Library sort field applied when resolving book details. */
  sortBy?: SortField;
  /** Library sort direction applied when resolving book details. */
  sortOrder?: SortOrder;
}

export interface UseShelfBooksViewResult {
  /** Accumulated list of books in the shelf. */
  books: Book[];
  /** Total number of books in the shelf (from shelves context when available). */
  total: number;
  /** Whether shelf books are currently being fetched. */
  isLoading: boolean;
  /** Error message if any. */
  error: string | null;
  /** Load the next page of shelf books. */
  loadMore?: () => void;
  /** Whether there are more pages to load. */
  hasMore?: boolean;
  /** Remove a book from the accumulated list (local only). */
  removeBook?: (bookId: number) => void;
}

interface ShelfBooksPage {
  refs: ShelfBookRef[];
  books: Book[];
}

async function fetchBooksByRefs(
  refs: ShelfBookRef[],
  full: boolean,
  sortBy: string = "timestamp",
  sortOrder: string = "desc",
): Promise<Book[]> {
  // Group refs by library_id
  const byLibrary = new Map<number, number[]>();
  for (const ref of refs) {
    const ids = byLibrary.get(ref.library_id) ?? [];
    ids.push(ref.book_id);
    byLibrary.set(ref.library_id, ids);
  }

  const allBooks: Book[] = [];

  for (const [libraryId, ids] of byLibrary) {
    const queryParams = new URLSearchParams({
      page: "1",
      page_size: Math.min(ids.length, 100).toString(),
      sort_by: sortBy,
      sort_order: sortOrder,
      include: "reading_summary",
    });

    if (full) {
      queryParams.append("full", "true");
    }
    if (libraryId) {
      queryParams.append("requested_library_id", libraryId.toString());
    }

    const filters = { ...createEmptyFilters(), titleIds: ids };
    const body = filtersToApiBody(filters);
    const url = `/api/books/filter?${queryParams.toString()}`;
    const fetchKey = generateFetchKey(url, {
      method: "POST",
      body: JSON.stringify(body),
    });

    const response = await deduplicateFetch(fetchKey, async () => {
      const resp = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
        cache: "no-store",
      });

      if (!resp.ok) {
        const errorData = (await resp.json()) as { detail?: string };
        throw new Error(errorData.detail || "Failed to fetch shelf books");
      }

      return (await resp.json()) as BookListResponse;
    });

    allBooks.push(...response.items);
  }

  return allBooks;
}

/**
 * Infinite-scroll shelf loader that does not assume shelf books are within the
 * "top N" of the library listing.
 *
 * Strategy
 * --------
 * - Page through `/api/shelves/:id/books` to get the shelf's ordered book IDs.
 * - For each page of IDs, resolve book details via `/api/books/filter` with
 *   `title_ids=[...]` for that page.
 * - Accumulate pages for infinite scroll.
 */
export function useShelfBooksView(
  options: UseShelfBooksViewOptions = {},
): UseShelfBooksViewResult {
  const {
    shelfId,
    pageSize = 20,
    full = false,
    shelfSortBy = "order",
    shelfSortOrder = "asc",
    sortBy = DEFAULT_SORT_FIELD,
    sortOrder = DEFAULT_SORT_ORDER,
  } = options;

  const { activeLibrary, isLoading: isActiveLibraryLoading } =
    useActiveLibrary();
  const hasActiveLibrary = activeLibrary !== null && !isActiveLibraryLoading;

  const { shelves } = useShelvesContext();
  const shelfTotal = useMemo(() => {
    if (!shelfId) return 0;
    const shelf = shelves.find((s) => s.id === shelfId);
    return shelf?.book_count ?? 0;
  }, [shelfId, shelves]);

  const enabled = !!shelfId && shelfId !== 0 && hasActiveLibrary;

  const queryKey = useMemo(
    () =>
      [
        "shelf-books-view",
        {
          shelfId,
          pageSize,
          full,
          shelfSortBy,
          shelfSortOrder,
          sortBy,
          sortOrder,
        },
      ] as const,
    [shelfId, pageSize, full, shelfSortBy, shelfSortOrder, sortBy, sortOrder],
  );

  const query = useInfiniteQuery<ShelfBooksPage, Error>({
    queryKey,
    initialPageParam: 1,
    enabled,
    queryFn: async ({ pageParam }) => {
      const page = (pageParam as number | undefined) ?? 1;

      const refs = await getShelfBooks(
        shelfId as number,
        page,
        shelfSortBy,
        pageSize,
        shelfSortOrder,
      );

      if (refs.length === 0) {
        return { refs: [], books: [] };
      }

      const books = await fetchBooksByRefs(refs, full, sortBy, sortOrder);
      return {
        refs,
        books,
      };
    },
    getNextPageParam: (lastPage, _allPages, lastPageParam) => {
      if (lastPage.refs.length < pageSize) {
        return undefined;
      }
      const current = (lastPageParam as number | undefined) ?? 1;
      return current + 1;
    },
    staleTime: 60_000,
  });

  const books = useMemo(
    () => query.data?.pages.flatMap((p) => p.books) ?? [],
    [query.data],
  );

  const queryClient = useQueryClient();
  const removeBook = useCallback(
    (bookId: number) => {
      queryClient.setQueryData<InfiniteData<ShelfBooksPage> | undefined>(
        queryKey,
        (prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            pages: prev.pages.map((p) => ({
              ...p,
              refs: p.refs.filter((ref) => ref.book_id !== bookId),
              books: p.books.filter((b) => b.id !== bookId),
            })),
          };
        },
      );
    },
    [queryClient, queryKey],
  );

  const loadMore = useCallback(() => {
    if (!query.hasNextPage) return;
    void query.fetchNextPage();
  }, [query]);

  const isLoading =
    isActiveLibraryLoading ||
    (enabled ? query.isPending || query.isFetching : false);

  const error =
    !isActiveLibraryLoading && !hasActiveLibrary
      ? "no_active_library"
      : (query.error?.message ?? null);

  return {
    books,
    total: shelfTotal || books.length,
    isLoading,
    error,
    loadMore: query.hasNextPage ? loadMore : undefined,
    hasMore: !!query.hasNextPage,
    removeBook,
  };
}
