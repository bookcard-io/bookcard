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

import { useCallback, useEffect, useMemo, useRef } from "react";
import { useBookDataUpdates } from "@/hooks/useBookDataUpdates";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";
import { useLibraryBooks } from "@/hooks/useLibraryBooks";
import type { Book } from "@/types/book";
import { deduplicateBooks } from "@/utils/books";
import { BookCard } from "./BookCard";
import { ShelfFilterInfoBox } from "./ShelfFilterInfoBox";
import type { FilterValues } from "./widgets/FiltersPanel";

export interface BooksGridProps {
  /** Callback fired when a book card is clicked. */
  onBookClick?: (book: Book) => void;
  /** Callback fired when a book edit button is clicked. */
  onBookEdit?: (bookId: number) => void;
  /** Search query to filter books. */
  searchQuery?: string;
  /** Filter values for advanced filtering. */
  filters?: FilterValues;
  /** Shelf ID to filter books by shelf. */
  shelfId?: number;
  /** Sort field. */
  sortBy?: "timestamp" | "pubdate" | "title" | "author_sort" | "series_index";
  /** Sort order. */
  sortOrder?: "asc" | "desc";
  /** Number of items per page. */
  pageSize?: number;
  /** Ref to expose methods for updating book data, cover, removing books, and adding books. */
  bookDataUpdateRef?: React.RefObject<{
    updateBook: (bookId: number, bookData: Partial<Book>) => void;
    updateCover: (bookId: number) => void;
    removeBook?: (bookId: number) => void;
    addBook?: (bookId: number) => Promise<void>;
  }>;
  /** Callback to expose book navigation data (bookIds, loadMore, hasMore, isLoading) for modal navigation. */
  onBooksDataChange?: (data: {
    bookIds: number[];
    loadMore?: () => void;
    hasMore?: boolean;
    isLoading: boolean;
  }) => void;
}

/**
 * Books grid component for displaying a paginated grid of books.
 *
 * Manages data fetching via useBooks hook and renders BookCard components.
 * Follows SOC by separating data fetching (hook) from presentation (component).
 */
export function BooksGrid({
  onBookClick,
  onBookEdit,
  searchQuery,
  filters,
  shelfId,
  sortBy,
  sortOrder,
  pageSize = 20,
  bookDataUpdateRef,
  onBooksDataChange,
}: BooksGridProps) {
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
    shelfId,
    sortBy,
    sortOrder,
    pageSize,
  });

  // Manage book data updates including cover (SRP: book data state management separated)
  const { bookDataOverrides } = useBookDataUpdates({
    updateRef: bookDataUpdateRef,
  });

  // Expose removeBook and addBook via ref so external callers can modify this grid instance
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

  // Infinite scroll handler (SRP: scroll logic separated)
  const handleLoadMore = useCallback(() => {
    loadMore?.();
  }, [loadMore]);

  // Set up infinite scroll sentinel (IOC: using hook for scroll behavior)
  const sentinelRef = useInfiniteScroll({
    onLoadMore: handleLoadMore,
    enabled: Boolean(loadMore && hasMore),
    isLoading,
    hasMore,
  });

  // Deduplicate books and apply book data overrides (DRY: using utility)
  const uniqueBooks = useMemo(
    () => deduplicateBooks(books, undefined, bookDataOverrides),
    [books, bookDataOverrides],
  );

  // Expose book navigation data to parent component for modal navigation
  // Use ref to avoid infinite loops from callback dependency changes
  const onBooksDataChangeRef = useRef(onBooksDataChange);
  useEffect(() => {
    onBooksDataChangeRef.current = onBooksDataChange;
  }, [onBooksDataChange]);

  // Memoize the data to avoid unnecessary updates
  const booksData = useMemo(
    () => ({
      bookIds: uniqueBooks.map((book) => book.id),
      loadMore,
      hasMore,
      isLoading,
    }),
    [uniqueBooks, loadMore, hasMore, isLoading],
  );

  // Store previous data to compare and only update if changed
  const prevBooksDataRef = useRef<typeof booksData | null>(null);
  useEffect(() => {
    const prev = prevBooksDataRef.current;
    const current = booksData;

    // Only call callback if data actually changed (or on first render)
    if (
      !prev ||
      prev.bookIds.length !== current.bookIds.length ||
      prev.bookIds.some((id, idx) => id !== current.bookIds[idx]) ||
      prev.hasMore !== current.hasMore ||
      prev.isLoading !== current.isLoading ||
      prev.loadMore !== current.loadMore
    ) {
      prevBooksDataRef.current = current;
      if (onBooksDataChangeRef.current) {
        onBooksDataChangeRef.current(current);
      }
    }
  }, [booksData]);

  // Handle deletion initiated from a card: remove locally from grid
  const handleBookDeleted = useCallback(
    (bookId: number) => {
      removeBook?.(bookId);
    },
    [removeBook],
  );

  if (error) {
    return (
      <div className="flex min-h-[400px] items-center justify-center p-8">
        <p className="m-0 text-base text-danger-a10">
          Error loading books: {error}
        </p>
      </div>
    );
  }

  if (isLoading && uniqueBooks.length === 0) {
    return (
      <div className="flex min-h-[400px] items-center justify-center p-8">
        <p className="m-0 text-base text-text-a40">Loading books...</p>
      </div>
    );
  }

  if (uniqueBooks.length === 0) {
    return (
      <div className="flex min-h-[400px] items-center justify-center p-8">
        <p className="m-0 text-base text-text-a40">No books found</p>
      </div>
    );
  }

  return (
    <div className="w-full">
      {total > 0 && (
        <div className="px-8 pb-4 text-left text-sm text-text-a40">
          {hasMore
            ? `Scroll for more (${uniqueBooks.length} of ${total})`
            : `${uniqueBooks.length} of ${total} books`}
        </div>
      )}
      {shelfId && <ShelfFilterInfoBox />}
      <div className="grid grid-cols-[repeat(auto-fit,minmax(140px,1fr))] gap-6 px-8 md:grid-cols-[repeat(auto-fit,minmax(160px,1fr))] md:gap-8 lg:grid-cols-[repeat(auto-fit,minmax(180px,1fr))]">
        {uniqueBooks.map((book) => (
          <BookCard
            key={book.id}
            book={book}
            allBooks={uniqueBooks}
            onClick={onBookClick}
            onEdit={onBookEdit}
            onBookDeleted={handleBookDeleted}
          />
        ))}
      </div>
      {hasMore && <div ref={sentinelRef as React.RefObject<HTMLDivElement>} />}
      {isLoading && uniqueBooks.length > 0 && (
        <div className="p-4 px-8 text-center text-sm text-text-a40">
          Loading more books...
        </div>
      )}
    </div>
  );
}
