"use client";

import { useCallback, useMemo } from "react";
import { useBooks } from "@/hooks/useBooks";
import { useFilteredBooks } from "@/hooks/useFilteredBooks";
import { useInfiniteScroll } from "@/hooks/useInfiniteScroll";
import type { Book } from "@/types/book";
import { hasActiveFilters } from "@/utils/filters";
import { BookCard } from "./BookCard";
import styles from "./BooksGrid.module.scss";
import type { FilterValues } from "./widgets/FiltersPanel";

export interface BooksGridProps {
  /** Callback fired when a book card is clicked. */
  onBookClick?: (book: Book) => void;
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
}

/**
 * Books grid component for displaying a paginated grid of books.
 *
 * Manages data fetching via useBooks hook and renders BookCard components.
 * Follows SOC by separating data fetching (hook) from presentation (component).
 */
export function BooksGrid({
  onBookClick,
  searchQuery,
  filters,
  sortBy,
  sortOrder,
  pageSize = 20,
}: BooksGridProps) {
  // Determine which filtering mechanism is active
  const filtersActive = hasActiveFilters(filters);
  const hasActiveSearch = searchQuery && searchQuery.trim().length > 0;

  // Use filtered books if filters are active, otherwise use search
  // Only one hook should be active at a time to avoid DRY violations and collisions
  // Priority: filters > search > all books
  const filteredBooksResult = useFilteredBooks({
    enabled: filtersActive, // Filters take priority, ignore search if both are active
    infiniteScroll: true,
    filters: filtersActive ? filters : undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
    page_size: pageSize,
  });

  const regularBooksResult = useBooks({
    enabled: !filtersActive, // Only run if filters are not active
    infiniteScroll: true,
    search: hasActiveSearch ? searchQuery : undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
    page_size: pageSize,
  });

  // Use filtered books if filters are active, otherwise use regular books
  // Regular books hook handles both search and "show all" cases
  const { books, isLoading, error, total, loadMore, hasMore } = filtersActive
    ? filteredBooksResult
    : regularBooksResult;

  // Infinite scroll handler
  const handleLoadMore = useCallback(() => {
    if (loadMore) {
      loadMore();
    }
  }, [loadMore]);

  // Set up infinite scroll sentinel
  const sentinelRef = useInfiniteScroll({
    onLoadMore: handleLoadMore,
    enabled: Boolean(loadMore && hasMore),
    isLoading,
    hasMore,
  });

  // Deduplicate books by ID as a safeguard (hooks should handle this, but defensive programming)
  const uniqueBooks = useMemo(() => {
    const seen = new Set<number>();
    return books.filter((book) => {
      if (seen.has(book.id)) {
        return false;
      }
      seen.add(book.id);
      return true;
    });
  }, [books]);

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
