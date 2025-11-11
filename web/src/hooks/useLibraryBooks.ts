import type { FilterValues } from "@/components/library/widgets/FiltersPanel";
import { useBooks } from "@/hooks/useBooks";
import { useFilteredBooks } from "@/hooks/useFilteredBooks";
import type { Book } from "@/types/book";
import { hasActiveFilters } from "@/utils/filters";

export interface UseLibraryBooksOptions {
  /** Filter values for advanced filtering. */
  filters?: FilterValues;
  /** Search query to filter books. */
  searchQuery?: string;
  /** Sort field. */
  sortBy?: "timestamp" | "pubdate" | "title" | "author_sort" | "series_index";
  /** Sort order. */
  sortOrder?: "asc" | "desc";
  /** Number of items per page. */
  pageSize?: number;
}

export interface UseLibraryBooksResult {
  /** List of books (accumulated if infinite scroll is enabled). */
  books: Book[];
  /** Total number of books. */
  total: number;
  /** Whether data is currently being fetched. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
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
 * Custom hook for fetching library books with filters, search, and sorting.
 *
 * Encapsulates the logic for determining which book fetching mechanism to use
 * (filtered vs regular) based on active filters and search query.
 * Eliminates DRY violations by centralizing book fetching logic.
 * Follows SRP by managing only book data fetching concerns.
 * Follows IOC by accepting configuration options.
 *
 * Parameters
 * ----------
 * options : UseLibraryBooksOptions
 *     Configuration for filters, search, sorting, and pagination.
 *
 * Returns
 * -------
 * UseLibraryBooksResult
 *     Books data, loading state, and control functions.
 */
export function useLibraryBooks(
  options: UseLibraryBooksOptions = {},
): UseLibraryBooksResult {
  const {
    filters,
    searchQuery,
    sortBy = "timestamp",
    sortOrder = "desc",
    pageSize = 20,
  } = options;

  // Determine which filtering mechanism is active
  // Priority: filters > search > all books
  const filtersActive = hasActiveFilters(filters);
  const hasActiveSearch = searchQuery && searchQuery.trim().length > 0;

  // Use filtered books if filters are active, otherwise use regular books
  const filteredBooksResult = useFilteredBooks({
    enabled: filtersActive,
    infiniteScroll: true,
    filters: filtersActive ? filters : undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
    page_size: pageSize,
  });

  const regularBooksResult = useBooks({
    enabled: !filtersActive,
    infiniteScroll: true,
    search: hasActiveSearch ? searchQuery : undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
    page_size: pageSize,
  });

  // Use filtered books if filters are active, otherwise use regular books
  const result = filtersActive ? filteredBooksResult : regularBooksResult;

  return {
    books: result.books,
    total: result.total,
    isLoading: result.isLoading,
    error: result.error,
    loadMore: result.loadMore,
    hasMore: result.hasMore,
    removeBook: result.removeBook,
    addBook: result.addBook,
  };
}
