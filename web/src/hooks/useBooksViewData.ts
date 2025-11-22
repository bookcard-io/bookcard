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

import { useEffect, useMemo } from "react";
import type { FilterValues } from "@/components/library/widgets/FiltersPanel";
import type { Book } from "@/types/book";
import { deduplicateBooks } from "@/utils/books";
import { useBookDataUpdates } from "./useBookDataUpdates";
import { useLibraryBooks } from "./useLibraryBooks";

export interface UseBooksViewDataOptions {
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
  /** Whether to fetch full book details. */
  full?: boolean;
  /** Ref to expose methods for updating book data, cover, removing books, and adding books. */
  bookDataUpdateRef?: React.RefObject<{
    updateBook: (bookId: number, bookData: Partial<Book>) => void;
    updateCover: (bookId: number) => void;
    removeBook?: (bookId: number) => void;
    addBook?: (bookId: number) => Promise<void>;
  } | null>;
}

export interface UseBooksViewDataResult {
  /** Deduplicated list of books. */
  uniqueBooks: Book[];
  /** Whether data is currently being fetched. */
  isLoading: boolean;
  /** Error message if fetch failed. */
  error: string | null;
  /** Total number of books. */
  total: number;
  /** Function to load next page. */
  loadMore?: () => void;
  /** Whether there are more pages to load. */
  hasMore?: boolean;
  /** Function to remove a book by ID. */
  removeBook?: (bookId: number) => void;
  /** Function to add a book by ID. */
  addBook?: (bookId: number) => Promise<void>;
  /** Function to update book data locally (for optimistic updates). */
  updateBook: (bookId: number, bookData: Partial<Book>) => void;
}

/**
 * Custom hook for managing books view data.
 *
 * Handles data fetching, deduplication, and ref exposure for book updates.
 * Follows SRP by managing only data concerns.
 * Follows IOC by accepting configuration options.
 * Follows DRY by centralizing common data management logic.
 *
 * Parameters
 * ----------
 * options : UseBooksViewDataOptions
 *     Configuration for filters, search, sorting, and ref exposure.
 *
 * Returns
 * -------
 * UseBooksViewDataResult
 *     Books data, loading state, and control functions.
 */
export function useBooksViewData(
  options: UseBooksViewDataOptions,
): UseBooksViewDataResult {
  const {
    filters,
    searchQuery,
    authorId,
    shelfId,
    sortBy,
    sortOrder,
    pageSize = 20,
    full = false,
    bookDataUpdateRef,
  } = options;

  // Fetch books using centralized hook (SOC: data fetching separated)
  const {
    books,
    isLoading,
    error,
    total,
    loadMore,
    hasMore,
    removeBook,
    addBook,
  } = useLibraryBooks({
    filters,
    searchQuery,
    authorId,
    shelfId,
    sortBy,
    sortOrder,
    pageSize,
    full,
  });

  // Manage book data updates including cover (SRP: book data state management separated)
  const { bookDataOverrides, updateBook } = useBookDataUpdates({
    updateRef: bookDataUpdateRef,
  });

  // Expose removeBook and addBook via ref so external callers can modify this instance
  useEffect(() => {
    if (!bookDataUpdateRef) {
      return;
    }
    const current = bookDataUpdateRef.current ?? {
      updateBook: () => {},
      updateCover: () => {},
    };
    bookDataUpdateRef.current = {
      ...current,
      removeBook: (bookId: number) => {
        removeBook?.(bookId);
      },
      addBook: async (bookId: number) => {
        await addBook?.(bookId);
      },
    };
  }, [bookDataUpdateRef, removeBook, addBook]);

  // Deduplicate books and apply book data overrides (DRY: using utility)
  const uniqueBooks = useMemo(
    () => deduplicateBooks(books, undefined, bookDataOverrides),
    [books, bookDataOverrides],
  );

  return {
    uniqueBooks,
    isLoading,
    error,
    total,
    loadMore,
    hasMore,
    removeBook,
    addBook,
    updateBook,
  };
}
