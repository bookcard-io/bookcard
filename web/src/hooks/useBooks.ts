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
import {
  useInfiniteQuery,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import type { Book, BookListResponse, BooksQueryParams } from "@/types/book";
import { deduplicateFetch, generateFetchKey } from "@/utils/fetch";

export interface UseBooksOptions extends BooksQueryParams {
  /** Whether to automatically fetch on mount. */
  enabled?: boolean;
  /** Whether to enable infinite scroll mode (accumulates books across pages). */
  infiniteScroll?: boolean;
  /** Whether to fetch full book details with all metadata. */
  full?: boolean;
}

export interface UseBooksResult {
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
  /** Function to update query parameters. */
  setQuery: (params: Partial<BooksQueryParams>) => void;
  /** Function to load next page (only available when infiniteScroll is enabled). */
  loadMore?: () => void;
  /** Whether there are more pages to load (only available when infiniteScroll is enabled). */
  hasMore?: boolean;
  /** Function to remove a book by ID from the accumulated books list. */
  removeBook?: (bookId: number) => void;
  /** Function to add a book by ID to the accumulated books list. */
  addBook?: (bookId: number) => Promise<void>;
}

interface FetchBooksPageParams {
  page: number;
  pageSize: number;
  search: string;
  sortBy: "timestamp" | "pubdate" | "title" | "author_sort" | "series_index";
  sortOrder: "asc" | "desc";
  full: boolean;
}

async function fetchBooksPage({
  page,
  pageSize,
  search,
  sortBy,
  sortOrder,
  full,
}: FetchBooksPageParams): Promise<BookListResponse> {
  const queryParams = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
    sort_by: sortBy,
    sort_order: sortOrder,
  });

  if (search.trim()) {
    queryParams.append("search", search.trim());
  }
  if (full) {
    queryParams.append("full", "true");
  }

  const url = `/api/books?${queryParams.toString()}`;
  const fetchKey = generateFetchKey(url, {
    method: "GET",
  });

  const result = await deduplicateFetch(fetchKey, async () => {
    const response = await fetch(url, {
      cache: "no-store",
    });

    if (!response.ok) {
      const errorData = (await response.json()) as { detail?: string };
      throw new Error(errorData.detail || "Failed to fetch books");
    }

    return (await response.json()) as BookListResponse;
  });

  return result;
}

/**
 * Custom hook for fetching and managing books data.
 *
 * Provides pagination, search, sorting, and loading state management.
 * Follows IOC pattern by accepting options and returning state/actions.
 *
 * @param options - Query parameters and options.
 * @returns Books data, loading state, and control functions.
 */
export function useBooks(options: UseBooksOptions = {}): UseBooksResult {
  const {
    enabled = true,
    infiniteScroll = false,
    page: initialPage = 1,
    page_size: initialPageSize = 20,
    search: initialSearch,
    sort_by: initialSortBy = "timestamp",
    sort_order: initialSortOrder = "desc",
    full = false,
  } = options;

  const { activeLibrary, isLoading: isActiveLibraryLoading } =
    useActiveLibrary();

  const [_page, _setPage] = useState(initialPage);
  const [_pageSize, _setPageSize] = useState(initialPageSize);
  const [_search, _setSearch] = useState(initialSearch || "");
  const [_sortBy, _setSortBy] = useState(initialSortBy);
  const [_sortOrder, _setSortOrder] = useState(initialSortOrder);

  const queryClient = useQueryClient();

  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [search, setSearch] = useState(initialSearch || "");
  const [sortBy, setSortBy] = useState(initialSortBy);
  const [sortOrder, setSortOrder] = useState(initialSortOrder);

  // Track previous prop values to detect changes
  const prevSearchRef = useRef<string | undefined>(initialSearch);
  const prevSortByRef = useRef<string | undefined>(initialSortBy);
  const prevSortOrderRef = useRef<string | undefined>(initialSortOrder);
  const prevPageSizeRef = useRef<number | undefined>(initialPageSize);

  // Sync internal state with prop changes
  useEffect(() => {
    const newSearch = options.search ?? "";
    if (options.search !== prevSearchRef.current) {
      prevSearchRef.current = options.search;
      setSearch(newSearch);
      setPage(1); // Reset to first page when search changes
    }
  }, [options.search]);

  useEffect(() => {
    if (options.sort_by !== prevSortByRef.current) {
      prevSortByRef.current = options.sort_by;
      if (options.sort_by !== undefined) {
        setSortBy(options.sort_by);
        setPage(1);
      }
    }
  }, [options.sort_by]);

  useEffect(() => {
    if (options.sort_order !== prevSortOrderRef.current) {
      prevSortOrderRef.current = options.sort_order;
      if (options.sort_order !== undefined) {
        setSortOrder(options.sort_order);
        setPage(1);
      }
    }
  }, [options.sort_order]);

  useEffect(() => {
    if (options.page_size !== prevPageSizeRef.current) {
      prevPageSizeRef.current = options.page_size;
      if (options.page_size !== undefined) {
        setPageSize(options.page_size);
        setPage(1); // Reset to first page when page size changes
      }
    }
  }, [options.page_size]);

  const listQueryKey = useMemo(
    () =>
      [
        "books",
        {
          page,
          pageSize,
          search,
          sortBy,
          sortOrder,
          full,
        },
      ] as const,
    [page, pageSize, search, sortBy, sortOrder, full],
  );

  const infiniteQueryKey = useMemo(
    () =>
      [
        "books-infinite",
        {
          pageSize,
          search,
          sortBy,
          sortOrder,
          full,
        },
      ] as const,
    [pageSize, search, sortBy, sortOrder, full],
  );

  // Only enable queries if there's an active library and not still loading
  const hasActiveLibrary = activeLibrary !== null && !isActiveLibraryLoading;
  const listQueryEnabled = enabled && !infiniteScroll && hasActiveLibrary;
  const infiniteQueryEnabled = enabled && infiniteScroll && hasActiveLibrary;

  const listQuery = useQuery<BookListResponse, Error>({
    queryKey: listQueryKey,
    queryFn: () =>
      fetchBooksPage({
        page,
        pageSize,
        search,
        sortBy,
        sortOrder,
        full,
      }),
    enabled: listQueryEnabled,
    staleTime: 60_000,
  });

  const infiniteQuery = useInfiniteQuery<BookListResponse, Error>({
    queryKey: infiniteQueryKey,
    queryFn: ({ pageParam }) =>
      fetchBooksPage({
        page: (pageParam as number | undefined) ?? 1,
        pageSize,
        search,
        sortBy,
        sortOrder,
        full,
      }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const currentPage = lastPage.page ?? 1;
      const totalPages = lastPage.total_pages ?? 0;
      return currentPage < totalPages ? currentPage + 1 : undefined;
    },
    enabled: infiniteQueryEnabled,
    staleTime: 60_000,
  });

  const setQuery = useCallback((params: Partial<BooksQueryParams>) => {
    if (params.page !== undefined) {
      setPage(params.page);
    }
    if (params.page_size !== undefined) {
      setPageSize(params.page_size);
      setPage(1); // Reset to first page when page size changes
    }
    if (params.search !== undefined) {
      setSearch(params.search);
      setPage(1); // Reset to first page when search changes
    }
    if (params.sort_by !== undefined) {
      setSortBy(params.sort_by);
      setPage(1);
    }
    if (params.sort_order !== undefined) {
      setSortOrder(params.sort_order);
      setPage(1);
    }
  }, []);

  const data = listQuery.data;
  const infiniteData = infiniteQuery.data;

  const books: Book[] = useMemo(() => {
    if (infiniteScroll) {
      if (!infiniteData) return [];
      const allItems = infiniteData.pages.flatMap(
        (pageData) => pageData?.items ?? [],
      );
      const seen = new Set<number>();
      return allItems.filter((book) => {
        if (seen.has(book.id)) return false;
        seen.add(book.id);
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

  const currentPage = useMemo(() => {
    if (infiniteScroll) {
      const pages = infiniteData?.pages;
      if (!pages || pages.length === 0) {
        return page;
      }
      const lastPage = pages[pages.length - 1];
      return lastPage?.page ?? page;
    }
    return data?.page ?? page;
  }, [infiniteScroll, infiniteData, data, page]);

  const currentPageSize = useMemo(() => {
    if (infiniteScroll) {
      const firstPage = infiniteData?.pages[0];
      return firstPage ? firstPage.page_size : pageSize;
    }
    return data?.page_size ?? pageSize;
  }, [infiniteScroll, infiniteData, data, pageSize]);

  const totalPages = useMemo(() => {
    if (infiniteScroll) {
      const firstPage = infiniteData?.pages[0];
      return firstPage ? firstPage.total_pages : 0;
    }
    return data?.total_pages ?? 0;
  }, [infiniteScroll, infiniteData, data]);

  const isLoading =
    isActiveLibraryLoading ||
    (infiniteScroll && infiniteQueryEnabled
      ? infiniteQuery.isPending || infiniteQuery.isFetching
      : listQueryEnabled
        ? listQuery.isPending || listQuery.isFetching
        : false);

  // Show friendly error if no active library, otherwise show API error
  const error =
    !isActiveLibraryLoading && !hasActiveLibrary
      ? "no_active_library"
      : (infiniteScroll && infiniteQuery.error?.message) ||
        listQuery.error?.message ||
        null;

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
    [infiniteScroll, queryClient, infiniteQueryKey, listQueryKey],
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
                page_size: pageSize,
                total_pages: 1,
              };
              return {
                pages: [newPage],
                pageParams: [1],
              };
            }

            const existing = prev.pages.some((pageData) =>
              pageData?.items.some((book) => book.id === newBook.id),
            );
            if (existing) {
              return prev;
            }

            if (prev.pages.length === 0) {
              const newPage: BookListResponse = {
                items: [newBook],
                total: 1,
                page: 1,
                page_size: pageSize,
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
                page_size: pageSize,
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
    [infiniteScroll, infiniteQueryKey, pageSize, queryClient],
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
    page: currentPage,
    pageSize: currentPageSize,
    totalPages,
    isLoading,
    error,
    refetch,
    setQuery,
    ...(infiniteScroll && { loadMore, hasMore, removeBook, addBook }),
  };
}
