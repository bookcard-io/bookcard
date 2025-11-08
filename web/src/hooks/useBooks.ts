"use client";

import { useCallback, useEffect, useState } from "react";
import type { Book, BookListResponse, BooksQueryParams } from "@/types/book";

export interface UseBooksOptions extends BooksQueryParams {
  /** Whether to automatically fetch on mount. */
  enabled?: boolean;
}

export interface UseBooksResult {
  /** List of books for current page. */
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
    page: initialPage = 1,
    page_size: initialPageSize = 20,
    search: initialSearch,
    sort_by: initialSortBy = "timestamp",
    sort_order: initialSortOrder = "desc",
  } = options;

  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const [search, setSearch] = useState(initialSearch || "");
  const [sortBy, setSortBy] = useState(initialSortBy);
  const [sortOrder, setSortOrder] = useState(initialSortOrder);

  const [data, setData] = useState<BookListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

      const response = await fetch(`/api/books?${queryParams.toString()}`, {
        cache: "no-store",
      });

      if (!response.ok) {
        const errorData = (await response.json()) as { detail?: string };
        throw new Error(errorData.detail || "Failed to fetch books");
      }

      const result = (await response.json()) as BookListResponse;
      setData(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, [enabled, page, pageSize, search, sortBy, sortOrder]);

  useEffect(() => {
    void fetchBooks();
  }, [fetchBooks]);

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
    }
    if (params.sort_order !== undefined) {
      setSortOrder(params.sort_order);
    }
  }, []);

  return {
    books: data?.items || [],
    total: data?.total || 0,
    page: data?.page || page,
    pageSize: data?.page_size || pageSize,
    totalPages: data?.total_pages || 0,
    isLoading,
    error,
    refetch: fetchBooks,
    setQuery,
  };
}
