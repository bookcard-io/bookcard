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

import { useCallback, useEffect, useRef, useState } from "react";
import type { Book, BookListResponse, BooksQueryParams } from "@/types/book";

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

  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [search, setSearch] = useState(initialSearch || "");
  const [sortBy, setSortBy] = useState(initialSortBy);
  const [sortOrder, setSortOrder] = useState(initialSortOrder);

  const [data, setData] = useState<BookListResponse | null>(null);
  const [accumulatedBooks, setAccumulatedBooks] = useState<Book[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      if (infiniteScroll) {
        setAccumulatedBooks([]); // Reset accumulated books when search changes
      }
    }
  }, [options.search, infiniteScroll]);

  useEffect(() => {
    if (options.sort_by !== prevSortByRef.current) {
      prevSortByRef.current = options.sort_by;
      if (options.sort_by !== undefined) {
        setSortBy(options.sort_by);
        if (infiniteScroll) {
          setAccumulatedBooks([]); // Reset accumulated books when sort changes
          setPage(1);
        }
      }
    }
  }, [options.sort_by, infiniteScroll]);

  useEffect(() => {
    if (options.sort_order !== prevSortOrderRef.current) {
      prevSortOrderRef.current = options.sort_order;
      if (options.sort_order !== undefined) {
        setSortOrder(options.sort_order);
        if (infiniteScroll) {
          setAccumulatedBooks([]); // Reset accumulated books when sort changes
          setPage(1);
        }
      }
    }
  }, [options.sort_order, infiniteScroll]);

  useEffect(() => {
    if (options.page_size !== prevPageSizeRef.current) {
      prevPageSizeRef.current = options.page_size;
      if (options.page_size !== undefined) {
        setPageSize(options.page_size);
        setPage(1); // Reset to first page when page size changes
      }
    }
  }, [options.page_size]);

  const fetchBooks = useCallback(async () => {
    if (!enabled) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
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

      const response = await fetch(`/api/books?${queryParams.toString()}`, {
        cache: "no-store",
      });

      if (!response.ok) {
        const errorData = (await response.json()) as { detail?: string };
        throw new Error(errorData.detail || "Failed to fetch books");
      }

      const result = (await response.json()) as BookListResponse;
      setData(result);

      // Accumulate books for infinite scroll
      if (infiniteScroll) {
        if (page === 1) {
          // First page: replace accumulated books
          setAccumulatedBooks(result.items);
        } else {
          // Subsequent pages: append to accumulated books, deduplicating by ID
          setAccumulatedBooks((prev) => {
            const existingIds = new Set(prev.map((book) => book.id));
            const newBooks = result.items.filter(
              (book) => !existingIds.has(book.id),
            );
            return [...prev, ...newBooks];
          });
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, [
    enabled,
    infiniteScroll,
    page,
    pageSize,
    search,
    sortBy,
    sortOrder,
    full,
  ]);

  useEffect(() => {
    void fetchBooks();
  }, [fetchBooks]);

  const setQuery = useCallback(
    (params: Partial<BooksQueryParams>) => {
      if (params.page !== undefined) {
        setPage(params.page);
      }
      if (params.page_size !== undefined) {
        setPageSize(params.page_size);
        setPage(1); // Reset to first page when page size changes
        if (infiniteScroll) {
          setAccumulatedBooks([]);
        }
      }
      if (params.search !== undefined) {
        setSearch(params.search);
        setPage(1); // Reset to first page when search changes
        if (infiniteScroll) {
          setAccumulatedBooks([]);
        }
      }
      if (params.sort_by !== undefined) {
        setSortBy(params.sort_by);
        if (infiniteScroll) {
          setAccumulatedBooks([]);
          setPage(1);
        }
      }
      if (params.sort_order !== undefined) {
        setSortOrder(params.sort_order);
        if (infiniteScroll) {
          setAccumulatedBooks([]);
          setPage(1);
        }
      }
    },
    [infiniteScroll],
  );

  const loadMore = useCallback(() => {
    if (!infiniteScroll || isLoading || !data) {
      return;
    }
    const currentPage = data.page || page;
    const totalPages = data.total_pages || 0;
    if (currentPage < totalPages) {
      setPage(currentPage + 1);
    }
  }, [infiniteScroll, isLoading, data, page]);

  const hasMore =
    infiniteScroll && data
      ? (data.page || page) < (data.total_pages || 0)
      : false;

  const books = infiniteScroll ? accumulatedBooks : data?.items || [];

  const removeBook = useCallback(
    (bookId: number) => {
      if (infiniteScroll) {
        setAccumulatedBooks((prev) =>
          prev.filter((book) => book.id !== bookId),
        );
      }
      // Also update data if it exists
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          items: prev.items.filter((book) => book.id !== bookId),
          total: Math.max(0, prev.total - 1),
        };
      });
    },
    [infiniteScroll],
  );

  const addBook = useCallback(
    async (bookId: number) => {
      if (!infiniteScroll) {
        return;
      }

      try {
        // Fetch the new book
        const response = await fetch(`/api/books/${bookId}`, {
          cache: "no-store",
        });

        if (!response.ok) {
          const errorData = (await response.json()) as { detail?: string };
          throw new Error(errorData.detail || "Failed to fetch book");
        }

        const newBook = (await response.json()) as Book;

        // Add to accumulated books (prepend since new books typically appear first)
        setAccumulatedBooks((prev) => {
          // Check if book already exists to avoid duplicates
          if (prev.some((book) => book.id === newBook.id)) {
            return prev;
          }
          return [newBook, ...prev];
        });

        // Also update data if it exists
        setData((prev) => {
          if (!prev) return prev;
          // Check if book already exists
          if (prev.items.some((book) => book.id === newBook.id)) {
            return prev;
          }
          return {
            ...prev,
            items: [newBook, ...prev.items],
            total: prev.total + 1,
          };
        });
      } catch (err) {
        // Silently fail - book will appear on next refresh
        console.error("Failed to add book to list:", err);
      }
    },
    [infiniteScroll],
  );

  return {
    books,
    total: data?.total || 0,
    page: data?.page || page,
    pageSize: data?.page_size || pageSize,
    totalPages: data?.total_pages || 0,
    isLoading,
    error,
    refetch: fetchBooks,
    setQuery,
    ...(infiniteScroll && { loadMore, hasMore, removeBook, addBook }),
  };
}
