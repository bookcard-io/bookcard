import { useCallback, useEffect, useState } from "react";
import type { FilterValues } from "@/components/library/widgets/FiltersPanel";
import type { Book, BookListResponse } from "@/types/book";
import { filtersToApiBody, hasActiveFilters } from "@/utils/filters";

export interface UseFilteredBooksOptions {
  /** Filter values. */
  filters?: FilterValues;
  /** Whether to automatically fetch on mount. */
  enabled?: boolean;
  /** Page number (1-indexed). */
  page?: number;
  /** Number of items per page. */
  page_size?: number;
  /** Sort field. */
  sort_by?: "timestamp" | "pubdate" | "title" | "author_sort" | "series_index";
  /** Sort order. */
  sort_order?: "asc" | "desc";
}

export interface UseFilteredBooksResult {
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
    filters,
    page: initialPage = 1,
    page_size: initialPageSize = 20,
    sort_by: initialSortBy = "timestamp",
    sort_order: initialSortOrder = "desc",
  } = options;

  const [data, setData] = useState<BookListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFilteredBooks = useCallback(async () => {
    if (!enabled || !filters) {
      return;
    }

    // Check if any filter is active
    if (!hasActiveFilters(filters)) {
      setData(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const queryParams = new URLSearchParams({
        page: initialPage.toString(),
        page_size: initialPageSize.toString(),
        sort_by: initialSortBy,
        sort_order: initialSortOrder,
      });

      const filterBody = filtersToApiBody(filters);

      const response = await fetch(
        `/api/books/filter?${queryParams.toString()}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(filterBody),
          cache: "no-store",
        },
      );

      if (!response.ok) {
        const errorData = (await response.json()) as { detail?: string };
        throw new Error(errorData.detail || "Failed to fetch filtered books");
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
  }, [
    enabled,
    filters,
    initialPage,
    initialPageSize,
    initialSortBy,
    initialSortOrder,
  ]);

  useEffect(() => {
    void fetchFilteredBooks();
  }, [fetchFilteredBooks]);

  return {
    books: data?.items || [],
    total: data?.total || 0,
    page: data?.page || initialPage,
    pageSize: data?.page_size || initialPageSize,
    totalPages: data?.total_pages || 0,
    isLoading,
    error,
    refetch: fetchFilteredBooks,
  };
}
