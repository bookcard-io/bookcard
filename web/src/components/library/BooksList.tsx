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

import { useCallback, useEffect, useMemo } from "react";
import { useBookDataUpdates } from "@/hooks/useBookDataUpdates";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";
import { useLibraryBooks } from "@/hooks/useLibraryBooks";
import type { Book } from "@/types/book";
import { deduplicateBooks } from "@/utils/books";
import { BookListItem } from "./BookListItem";
import { ListHeader } from "./ListHeader";
import { ColumnSelectorButton } from "./widgets/ColumnSelectorButton";
import type { FilterValues } from "./widgets/FiltersPanel";

export interface BooksListProps {
  /** Callback fired when a book item is clicked. */
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
 * Books list component for displaying a paginated list of books.
 *
 * Manages data fetching via useLibraryBooks hook and renders BookListItem components.
 * Follows SOC by separating data fetching (hook) from presentation (component).
 */
export function BooksList({
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
}: BooksListProps) {
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
    full: true, // Always fetch full details for list view to support additional columns
  });

  // Manage book data updates including cover (SRP: book data state management separated)
  const { bookDataOverrides, updateBook: updateBookLocal } = useBookDataUpdates(
    {
      updateRef: bookDataUpdateRef,
    },
  );

  // Expose removeBook and addBook via ref so external callers can modify this list instance
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
  useEffect(() => {
    if (onBooksDataChange) {
      const bookIds = uniqueBooks.map((book) => book.id);
      onBooksDataChange({
        bookIds,
        loadMore,
        hasMore,
        isLoading,
      });
    }
  }, [onBooksDataChange, uniqueBooks, loadMore, hasMore, isLoading]);

  // Handle deletion initiated from an item: remove locally from list
  const handleBookDeleted = useCallback(
    (bookId: number) => {
      removeBook?.(bookId);
    },
    [removeBook],
  );

  // Handle rating change: update via API and local state
  const handleRatingChange = useCallback(
    async (bookId: number, rating: number | null) => {
      // Optimistically update local state
      updateBookLocal(bookId, { rating });

      // Update via API
      try {
        const response = await fetch(`/api/books/${bookId}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            rating_value: rating,
          }),
        });

        if (!response.ok) {
          // Revert on error - could be enhanced with error handling
          const errorData = (await response.json()) as { detail?: string };
          console.error(
            "Failed to update rating:",
            errorData.detail || "Unknown error",
          );
        }
      } catch (error) {
        console.error("Error updating rating:", error);
      }
    },
    [updateBookLocal],
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
    <div className="w-full py-6">
      {total > 0 && (
        <div className="flex items-center justify-between px-8 pb-4">
          <div className="text-left text-sm text-text-a40">
            {hasMore
              ? `Scroll for more (${uniqueBooks.length} of ${total})`
              : `${uniqueBooks.length} of ${total} books`}
          </div>
          <div className="flex items-center">
            <ColumnSelectorButton />
          </div>
        </div>
      )}
      <div className="flex flex-col px-8">
        <ListHeader allBooks={uniqueBooks} />
        {uniqueBooks.map((book) => (
          <BookListItem
            key={book.id}
            book={book}
            allBooks={uniqueBooks}
            onClick={onBookClick}
            onEdit={onBookEdit}
            onBookDeleted={handleBookDeleted}
            onRatingChange={handleRatingChange}
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
