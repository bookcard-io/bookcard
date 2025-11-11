"use client";

import { useCallback, useEffect, useMemo } from "react";
import { useBookDataUpdates } from "@/hooks/useBookDataUpdates";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";
import { useLibraryBooks } from "@/hooks/useLibraryBooks";
import type { Book } from "@/types/book";
import { deduplicateBooks } from "@/utils/books";
import { BookCard } from "./BookCard";
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
  /** Sort field. */
  sortBy?: "timestamp" | "pubdate" | "title" | "author_sort" | "series_index";
  /** Sort order. */
  sortOrder?: "asc" | "desc";
  /** Number of items per page. */
  pageSize?: number;
  /** Ref to expose methods for updating book data, cover, and removing books. */
  bookDataUpdateRef?: React.RefObject<{
    updateBook: (bookId: number, bookData: Partial<Book>) => void;
    updateCover: (bookId: number) => void;
    removeBook?: (bookId: number) => void;
  }>;
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
  sortBy,
  sortOrder,
  pageSize = 20,
  bookDataUpdateRef,
}: BooksGridProps) {
  // Fetch books using centralized hook (SOC: data fetching separated)
  const { books, isLoading, error, total, loadMore, hasMore, removeBook } =
    useLibraryBooks({
      filters,
      searchQuery,
      sortBy,
      sortOrder,
      pageSize,
    });

  // Manage book data updates including cover (SRP: book data state management separated)
  const { bookDataOverrides } = useBookDataUpdates({
    updateRef: bookDataUpdateRef,
  });

  // Expose removeBook via ref so external callers (e.g., modal) can remove from this grid instance
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
    };
    // We only need to update when the removeBook function identity changes
  }, [bookDataUpdateRef, removeBook]);

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
    <div className="w-full py-6">
      {total > 0 && (
        <div className="px-8 pb-4 text-left text-sm text-text-a40">
          {hasMore
            ? `Scroll for more (${uniqueBooks.length} of ${total})`
            : `${uniqueBooks.length} of ${total} books`}
        </div>
      )}
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
