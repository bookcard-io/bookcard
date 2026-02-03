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

import { useEffect } from "react";
import type { FilterValues } from "@/components/library/widgets/FiltersPanel";
import { useLibraryLoading } from "@/contexts/LibraryLoadingContext";
import { useBooks } from "@/hooks/useBooks";
import { useFilteredBooks } from "@/hooks/useFilteredBooks";
import { useShelfBooksView } from "@/hooks/useShelfBooksView";
import type { Book } from "@/types/book";
import { hasActiveFilters } from "@/utils/filters";

export interface UseLibraryBooksOptions {
  /** Filter values for advanced filtering. */
  filters?: FilterValues;
  /** Search query to filter books. */
  searchQuery?: string;
  /** Author ID to filter books by author (alternative to search). */
  authorId?: number;
  /** Shelf ID to filter books by shelf. */
  shelfId?: number;
  /** Sort field. */
  sortBy?: "timestamp" | "pubdate" | "title" | "author_sort" | "series_index";
  /** Sort order. */
  sortOrder?: "asc" | "desc";
  /** Number of items per page. */
  pageSize?: number;
  /** Whether to fetch full book details with all metadata. */
  full?: boolean;
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
    authorId,
    shelfId,
    sortBy = "timestamp",
    sortOrder = "desc",
    pageSize = 20,
    full = false,
  } = options;

  // Determine which filtering mechanism is active
  // Priority: shelf > filters > search > all books
  const filtersActive = hasActiveFilters(filters);
  const hasActiveSearch = searchQuery && searchQuery.trim().length > 0;
  const hasShelfFilter = shelfId !== undefined;

  // Use filtered books if filters are active, otherwise use regular books
  const filteredBooksResult = useFilteredBooks({
    enabled: filtersActive && !hasShelfFilter,
    infiniteScroll: true,
    filters: filtersActive ? filters : undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
    page_size: pageSize,
    full,
  });

  const regularBooksResult = useBooks({
    enabled: !filtersActive && !hasShelfFilter,
    infiniteScroll: true,
    search: hasActiveSearch ? searchQuery : undefined,
    author_id: authorId,
    sort_by: sortBy,
    sort_order: sortOrder,
    page_size: pageSize,
    full,
  });

  const shelfBooksViewResult = useShelfBooksView({
    shelfId: hasShelfFilter ? shelfId : undefined,
    pageSize,
    full,
    // Preserve existing shelf endpoint behavior (order asc) for now.
    // This avoids relying on `/api/books` ordering and supports infinite scroll.
    shelfSortBy: "order",
    shelfSortOrder: "asc",
  });

  // Base result: use filtered books if filters are active, otherwise use regular books
  const baseResult = filtersActive ? filteredBooksResult : regularBooksResult;

  // Determine which result to use
  const result = hasShelfFilter
    ? {
        books: shelfBooksViewResult.books,
        total: shelfBooksViewResult.total,
        isLoading: shelfBooksViewResult.isLoading,
        error: shelfBooksViewResult.error,
        loadMore: shelfBooksViewResult.loadMore,
        hasMore: shelfBooksViewResult.hasMore,
        removeBook: shelfBooksViewResult.removeBook,
        addBook: undefined,
      }
    : baseResult;

  const { incrementBooksLoading, decrementBooksLoading } = useLibraryLoading();

  // Integrate with global library loading context while keeping book data
  // fetching concerns localized to this hook. Uses a reference-counted
  // model so multiple hook instances can contribute to the shared signal.
  useEffect(() => {
    if (result.isLoading) {
      incrementBooksLoading();
      return () => {
        decrementBooksLoading();
      };
    }
    return undefined;
  }, [result.isLoading, incrementBooksLoading, decrementBooksLoading]);

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
