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

import type { InfiniteData } from "@tanstack/react-query";
import {
  useInfiniteQuery,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { FilterValues } from "@/components/library/widgets/FiltersPanel";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import type { Book, BookListResponse } from "@/types/book";
import { deduplicateFetch, generateFetchKey } from "@/utils/fetch";
import { filtersToApiBody, hasActiveFilters } from "@/utils/filters";

export interface UseFilteredBooksOptions {
  /** Filter values. */
  filters?: FilterValues;
  /** Whether to automatically fetch on mount. */
  enabled?: boolean;
  /** Whether to enable infinite scroll mode (accumulates books across pages). */
  infiniteScroll?: boolean;
  /** Page number (1-indexed). */
  page?: number;
  /** Number of items per page. */
  page_size?: number;
  /** Sort field. */
  sort_by?: "timestamp" | "pubdate" | "title" | "author_sort" | "series_index";
  /** Sort order. */
  sort_order?: "asc" | "desc";
  /** Whether to fetch full book details with all metadata. */
  full?: boolean;
}

export interface UseFilteredBooksResult {
  /** List of books (accumulated if infinite scroll is enabled). */
  books: Book[];
  /** Total number of books. */
  total: number;
  /** Current page number. */
  page: number;
  /** Number of items per page. */
  pageSize: number;
  /** Total number of pages. */
  totalPages: number;
  /** Whether data is currently being fetched. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** Function to refetch books. */
  refetch: () => Promise<void>;
  /** Function to remove a book by ID from the list. */
  removeBook: (bookId: number) => void;
  /** Function to load next page (only available when infiniteScroll is enabled). */
  loadMore?: () => void;
  /** Whether there are more pages to load (only available when infiniteScroll is enabled). */
  hasMore?: boolean;
  /** Function to add a book by ID to the accumulated books list. */
  addBook?: (bookId: number) => Promise<void>;
}

interface FetchFilteredBooksPageParams {
  filters: FilterValues;
  page: number;
  pageSize: number;
  sortBy: "timestamp" | "pubdate" | "title" | "author_sort" | "series_index";
  sortOrder: "asc" | "desc";
  full: boolean;
  libraryId?: number | null;
}

async function fetchFilteredBooksPage({
  filters,
  page,
  pageSize,
  sortBy,
  sortOrder,
  full,
  libraryId,
}: FetchFilteredBooksPageParams): Promise<BookListResponse> {
  // Check if any filter is active
  if (!hasActiveFilters(filters)) {
    return {
      items: [],
      total: 0,
      page: 1,
      page_size: pageSize,
      total_pages: 0,
    };
  }

  const queryParams = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
    sort_by: sortBy,
    sort_order: sortOrder,
    include: "reading_summary",
  });

  if (full) {
    queryParams.append("full", "true");
  }
  if (libraryId != null) {
    queryParams.append("library_id", libraryId.toString());
  }

  const filterBody = filtersToApiBody(filters);
  const url = `/api/books/filter?${queryParams.toString()}`;
  const fetchKey = generateFetchKey(url, {
    method: "POST",
    body: JSON.stringify(filterBody),
  });

  const result = await deduplicateFetch(fetchKey, async () => {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(filterBody),
      cache: "no-store",
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail || "Failed to fetch filtered books");
    }

    return (await response.json()) as BookListResponse;
  });

  return result;
}

/**
 * Custom hook for fetching and managing filtered books data.
 *
 * Provides pagination, filtering, sorting, and loading state management.
 * Follows IOC pattern by accepting options and returning state/actions.
 *
 * Parameters
 * ----------
 * options : UseFilteredBooksOptions
 *     Query parameters and options.
 *
 * Returns
 * -------
 * UseFilteredBooksResult
 *     Books data, loading state, and control functions.
 */
export function useFilteredBooks(
  options: UseFilteredBooksOptions = {},
): UseFilteredBooksResult {
  const {
    enabled = true,
    infiniteScroll = false,
    filters,
    page: initialPage = 1,
    page_size: initialPageSize = 20,
    sort_by: initialSortBy = "timestamp",
    sort_order: initialSortOrder = "desc",
    full = false,
  } = options;

  const {
    activeLibrary,
    isLoading: isActiveLibraryLoading,
    selectedLibraryId,
  } = useActiveLibrary();

  const queryClient = useQueryClient();

  const [data, _setData] = useState<BookListResponse | null>(null);
  const [accumulatedBooks, setAccumulatedBooks] = useState<Book[]>([]);
  const [isLoading, _setIsLoading] = useState(false);
  const [error, _setError] = useState<string | null>(null);

  // Track previous prop values to detect changes
  const prevSortByRef = useRef<string | undefined>(initialSortBy);
  const prevSortOrderRef = useRef<string | undefined>(initialSortOrder);
  const prevPageSizeRef = useRef<number | undefined>(initialPageSize);
  const prevFiltersRef = useRef<FilterValues | undefined>(filters);

  // Use current values from options, not initial values
  const currentSortBy = options.sort_by ?? initialSortBy;
  const currentSortOrder = options.sort_order ?? initialSortOrder;
  const currentPageSize = options.page_size ?? initialPageSize;
  const [currentPage, setCurrentPage] = useState(options.page ?? initialPage);

  // Reset accumulated books when filters, sort, or page size change
  useEffect(() => {
    if (!infiniteScroll) {
      return;
    }

    const filtersChanged = filters !== prevFiltersRef.current;
    const sortByChanged = currentSortBy !== prevSortByRef.current;
    const sortOrderChanged = currentSortOrder !== prevSortOrderRef.current;
    const pageSizeChanged = currentPageSize !== prevPageSizeRef.current;

    if (
      filtersChanged ||
      sortByChanged ||
      sortOrderChanged ||
      pageSizeChanged
    ) {
      setAccumulatedBooks([]);
      setCurrentPage(1);
      prevFiltersRef.current = filters;
      prevSortByRef.current = currentSortBy;
      prevSortOrderRef.current = currentSortOrder;
      prevPageSizeRef.current = currentPageSize;
    }
  }, [
    infiniteScroll,
    filters,
    currentSortBy,
    currentSortOrder,
    currentPageSize,
  ]);

  // Sync when options change
  useEffect(() => {
    if (options.sort_by !== prevSortByRef.current) {
      prevSortByRef.current = options.sort_by;
    }
  }, [options.sort_by]);

  useEffect(() => {
    if (options.sort_order !== prevSortOrderRef.current) {
      prevSortOrderRef.current = options.sort_order;
    }
  }, [options.sort_order]);

  useEffect(() => {
    if (options.page_size !== prevPageSizeRef.current) {
      prevPageSizeRef.current = options.page_size;
    }
  }, [options.page_size]);

  const listQueryKey = useMemo(
    () =>
      [
        "filtered-books",
        {
          filters,
          page: currentPage,
          pageSize: currentPageSize,
          sortBy: currentSortBy,
          sortOrder: currentSortOrder,
          full,
          selectedLibraryId,
        },
      ] as const,
    [
      filters,
      currentPage,
      currentPageSize,
      currentSortBy,
      currentSortOrder,
      full,
      selectedLibraryId,
    ],
  );

  const infiniteQueryKey = useMemo(
    () =>
      [
        "filtered-books-infinite",
        {
          filters,
          pageSize: currentPageSize,
          sortBy: currentSortBy,
          sortOrder: currentSortOrder,
          full,
          selectedLibraryId,
        },
      ] as const,
    [
      filters,
      currentPageSize,
      currentSortBy,
      currentSortOrder,
      full,
      selectedLibraryId,
    ],
  );

  // Only enable queries if there's an active library and not still loading
  const hasActiveLibrary = activeLibrary !== null && !isActiveLibraryLoading;
  const listQueryEnabled =
    enabled && !!filters && !infiniteScroll && hasActiveLibrary;
  const infiniteQueryEnabled =
    enabled && !!filters && infiniteScroll && hasActiveLibrary;

  const listQuery = useQuery<BookListResponse, Error>({
    queryKey: listQueryKey,
    queryFn: () =>
      fetchFilteredBooksPage({
        filters: filters as FilterValues,
        page: currentPage,
        pageSize: currentPageSize,
        sortBy: currentSortBy,
        sortOrder: currentSortOrder,
        full,
        libraryId: selectedLibraryId,
      }),
    enabled: listQueryEnabled && !!filters && hasActiveFilters(filters),
    staleTime: 60_000,
  });

  const infiniteQuery = useInfiniteQuery<
    BookListResponse,
    Error,
    InfiniteData<BookListResponse>,
    readonly unknown[],
    number
  >({
    queryKey: infiniteQueryKey,
    queryFn: ({ pageParam = 1 }) =>
      fetchFilteredBooksPage({
        filters: filters as FilterValues,
        page: pageParam,
        pageSize: currentPageSize,
        sortBy: currentSortBy,
        sortOrder: currentSortOrder,
        full,
        libraryId: selectedLibraryId,
      }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const pageNum = lastPage.page ?? 1;
      const totalPages = lastPage.total_pages ?? 0;
      return pageNum < totalPages ? pageNum + 1 : undefined;
    },
    enabled:
      infiniteQueryEnabled &&
      !!filters &&
      hasActiveFilters(filters as FilterValues),
    staleTime: 60_000,
  });

  const infiniteData = infiniteQuery.data;
  const effectiveData = listQuery.data ?? data;

  const effectiveIsLoading =
    isActiveLibraryLoading ||
    (infiniteScroll && infiniteQueryEnabled
      ? infiniteQuery.isPending || infiniteQuery.isFetching
      : listQueryEnabled
        ? listQuery.isPending || listQuery.isFetching
        : false) ||
    isLoading;

  // Show friendly error if no active library, otherwise show API error
  const effectiveError =
    !isActiveLibraryLoading && !hasActiveLibrary
      ? "no_active_library"
      : (infiniteQuery.error?.message ??
        listQuery.error?.message ??
        error ??
        null);

  const books: Book[] = useMemo(() => {
    if (infiniteScroll) {
      if (!infiniteData) return accumulatedBooks.length ? accumulatedBooks : [];
      const allItems = infiniteData.pages.flatMap((pageData) => pageData.items);
      const seen = new Set<number>();
      return allItems.filter((book) => {
        if (seen.has(book.id)) return false;
        seen.add(book.id);
        return true;
      });
    }
    return effectiveData?.items ?? [];
  }, [infiniteScroll, infiniteData, effectiveData, accumulatedBooks]);

  const total = useMemo(() => {
    if (infiniteScroll) {
      const firstPage = infiniteData?.pages[0];
      return firstPage ? firstPage.total : (effectiveData?.total ?? 0);
    }
    return effectiveData?.total ?? 0;
  }, [infiniteScroll, infiniteData, effectiveData]);

  const page = useMemo(() => {
    if (infiniteScroll) {
      const pages = infiniteData?.pages;
      if (!pages || pages.length === 0) {
        return currentPage;
      }
      const lastPage = pages[pages.length - 1];
      return lastPage?.page ?? currentPage;
    }
    return effectiveData?.page ?? currentPage;
  }, [infiniteScroll, infiniteData, effectiveData, currentPage]);

  const pageSize = useMemo(() => {
    if (infiniteScroll) {
      const firstPage = infiniteData?.pages[0];
      return firstPage ? firstPage.page_size : currentPageSize;
    }
    return effectiveData?.page_size ?? currentPageSize;
  }, [infiniteScroll, infiniteData, effectiveData, currentPageSize]);

  const totalPages = useMemo(() => {
    if (infiniteScroll) {
      const firstPage = infiniteData?.pages[0];
      return firstPage ? firstPage.total_pages : 0;
    }
    return effectiveData?.total_pages ?? 0;
  }, [infiniteScroll, infiniteData, effectiveData]);

  const loadMore = useCallback(() => {
    if (!infiniteScroll || !infiniteQueryEnabled) {
      return;
    }
    if (!infiniteQuery.hasNextPage) {
      return;
    }
    void infiniteQuery.fetchNextPage();
  }, [infiniteScroll, infiniteQuery, infiniteQueryEnabled]);

  const hasMore = !!(
    infiniteScroll &&
    infiniteQueryEnabled &&
    infiniteQuery.hasNextPage
  );

  const removeBook = useCallback(
    (bookId: number) => {
      if (infiniteScroll) {
        queryClient.setQueryData<InfiniteData<BookListResponse> | undefined>(
          infiniteQueryKey,
          (prev) => {
            if (!prev) return prev;
            let removedCount = 0;
            const newPages = prev.pages.map((pageData) => {
              const originalLength = pageData.items.length;
              const filteredItems = pageData.items.filter(
                (book) => book.id !== bookId,
              );
              if (filteredItems.length !== originalLength) {
                removedCount += originalLength - filteredItems.length;
                return {
                  ...pageData,
                  items: filteredItems,
                };
              }
              return pageData;
            });
            if (!removedCount || newPages.length === 0) {
              return prev;
            }
            const [firstPage, ...restPages] = newPages;
            if (!firstPage) {
              return prev;
            }
            const updatedFirstPage: BookListResponse = {
              items: firstPage.items,
              total: Math.max(0, firstPage.total - removedCount),
              page: firstPage.page,
              page_size: firstPage.page_size,
              total_pages: firstPage.total_pages,
            };
            return {
              ...prev,
              pages: [updatedFirstPage, ...restPages],
            };
          },
        );
      } else {
        queryClient.setQueryData<BookListResponse | undefined>(
          listQueryKey,
          (prev) => {
            if (!prev) return prev;
            const filteredItems: Book[] = prev.items.filter(
              (book: Book) => book.id !== bookId,
            );
            if (filteredItems.length === prev.items.length) {
              return prev;
            }
            return {
              ...prev,
              items: filteredItems,
              total: Math.max(0, prev.total - 1),
            };
          },
        );
      }
    },
    [infiniteScroll, infiniteQueryKey, listQueryKey, queryClient],
  );

  const addBook = useCallback(
    async (bookId: number) => {
      if (!infiniteScroll) {
        return;
      }

      try {
        const response = await fetch(`/api/books/${bookId}`, {
          cache: "no-store",
        });

        if (!response.ok) {
          const errorData = (await response.json()) as { detail?: string };
          throw new Error(errorData.detail || "Failed to fetch book");
        }

        const newBook = (await response.json()) as Book;

        queryClient.setQueryData<InfiniteData<BookListResponse> | undefined>(
          infiniteQueryKey,
          (prev) => {
            if (!prev) {
              const newPage: BookListResponse = {
                items: [newBook],
                total: 1,
                page: 1,
                page_size: currentPageSize,
                total_pages: 1,
              };
              return {
                pages: [newPage],
                pageParams: [1],
              };
            }

            const exists = prev.pages.some((pageData) =>
              pageData.items.some((book) => book.id === newBook.id),
            );
            if (exists) {
              return prev;
            }

            if (prev.pages.length === 0) {
              const newPage: BookListResponse = {
                items: [newBook],
                total: 1,
                page: 1,
                page_size: currentPageSize,
                total_pages: 1,
              };
              return {
                pages: [newPage],
                pageParams: [1],
              };
            }

            const [firstPage, ...restPages] = prev.pages;
            if (!firstPage) {
              const newPage: BookListResponse = {
                items: [newBook],
                total: 1,
                page: 1,
                page_size: currentPageSize,
                total_pages: 1,
              };
              return {
                pages: [newPage],
                pageParams: [1],
              };
            }
            const updatedFirstPage: BookListResponse = {
              items: [newBook, ...firstPage.items],
              total: firstPage.total + 1,
              page: firstPage.page,
              page_size: firstPage.page_size,
              total_pages: firstPage.total_pages,
            };

            return {
              ...prev,
              pages: [updatedFirstPage, ...restPages],
            };
          },
        );
      } catch (err) {
        console.error("Failed to add book to list:", err);
      }
    },
    [infiniteScroll, infiniteQueryKey, currentPageSize, queryClient],
  );

  const refetch = useCallback(async () => {
    if (infiniteScroll) {
      await infiniteQuery.refetch();
    } else {
      await listQuery.refetch();
    }
  }, [infiniteScroll, infiniteQuery, listQuery]);

  return {
    books,
    total,
    page,
    pageSize,
    totalPages,
    isLoading: effectiveIsLoading,
    error: effectiveError,
    refetch,
    removeBook,
    ...(infiniteScroll && { loadMore, hasMore, addBook }),
  };
}
