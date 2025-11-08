import { useCallback, useEffect, useRef, useState } from "react";
import type { FilterValues } from "@/components/library/widgets/FiltersPanel";
import type { Book, BookListResponse } from "@/types/book";
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
  /** Function to load next page (only available when infiniteScroll is enabled). */
  loadMore?: () => void;
  /** Whether there are more pages to load (only available when infiniteScroll is enabled). */
  hasMore?: boolean;
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
  } = options;

  const [data, setData] = useState<BookListResponse | null>(null);
  const [accumulatedBooks, setAccumulatedBooks] = useState<Book[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
        page: currentPage.toString(),
        page_size: currentPageSize.toString(),
        sort_by: currentSortBy,
        sort_order: currentSortOrder,
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

      // Accumulate books for infinite scroll
      if (infiniteScroll) {
        if (currentPage === 1) {
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
    filters,
    currentPage,
    currentPageSize,
    currentSortBy,
    currentSortOrder,
  ]);

  useEffect(() => {
    void fetchFilteredBooks();
  }, [fetchFilteredBooks]);

  const loadMore = useCallback(() => {
    if (!infiniteScroll || isLoading || !data) {
      return;
    }
    const pageNum = data.page || currentPage;
    const totalPages = data.total_pages || 0;
    if (pageNum < totalPages) {
      setCurrentPage(pageNum + 1);
    }
  }, [infiniteScroll, isLoading, data, currentPage]);

  const hasMore =
    infiniteScroll && data
      ? (data.page || currentPage) < (data.total_pages || 0)
      : false;

  const books = infiniteScroll ? accumulatedBooks : data?.items || [];

  return {
    books,
    total: data?.total || 0,
    page: data?.page || currentPage,
    pageSize: data?.page_size || currentPageSize,
    totalPages: data?.total_pages || 0,
    isLoading,
    error,
    refetch: fetchFilteredBooks,
    ...(infiniteScroll && { loadMore, hasMore }),
  };
}
