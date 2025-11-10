"use client";

import { useCallback, useMemo } from "react";
import { useBookDataUpdates } from "@/hooks/useBookDataUpdates";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";
import { useLibraryBooks } from "@/hooks/useLibraryBooks";
import type { Book } from "@/types/book";
import { deduplicateBooks } from "@/utils/books";
import { BookCard } from "./BookCard";
import styles from "./BooksGrid.module.scss";
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
  /** Ref to expose methods for updating book data and cover. */
  bookDataUpdateRef?: React.RefObject<{
    updateBook: (bookId: number, bookData: Partial<Book>) => void;
    updateCover: (bookId: number) => void;
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
  const { books, isLoading, error, total, loadMore, hasMore } = useLibraryBooks(
    {
      filters,
      searchQuery,
      sortBy,
      sortOrder,
      pageSize,
    },
  );

  // Manage book data updates including cover (SRP: book data state management separated)
  const { bookDataOverrides } = useBookDataUpdates({
    updateRef: bookDataUpdateRef,
  });

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

  if (error) {
    return (
      <div className={styles.errorContainer}>
        <p className={styles.errorMessage}>Error loading books: {error}</p>
      </div>
    );
  }

  if (isLoading && uniqueBooks.length === 0) {
    return (
      <div className={styles.loadingContainer}>
        <p className={styles.loadingMessage}>Loading books...</p>
      </div>
    );
  }

  if (uniqueBooks.length === 0) {
    return (
      <div className={styles.emptyContainer}>
        <p className={styles.emptyMessage}>No books found</p>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {total > 0 && (
        <div className={styles.paginationInfo}>
          {hasMore
            ? `Scroll for more (${uniqueBooks.length} of ${total})`
            : `${uniqueBooks.length} of ${total} books`}
        </div>
      )}
      <div className={styles.grid}>
        {uniqueBooks.map((book) => (
          <BookCard
            key={book.id}
            book={book}
            allBooks={uniqueBooks}
            onClick={onBookClick}
            onEdit={onBookEdit}
          />
        ))}
      </div>
      {hasMore && <div ref={sentinelRef as React.RefObject<HTMLDivElement>} />}
      {isLoading && uniqueBooks.length > 0 && (
        <div className={styles.loadingMore}>Loading more books...</div>
      )}
    </div>
  );
}
