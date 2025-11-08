"use client";

import { useBooks } from "@/hooks/useBooks";
import type { Book } from "@/types/book";
import { BookCard } from "./BookCard";
import styles from "./BooksGrid.module.scss";

export interface BooksGridProps {
  /** Callback fired when a book card is clicked. */
  onBookClick?: (book: Book) => void;
  /** Search query to filter books. */
  searchQuery?: string;
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
  sortBy,
  sortOrder,
  pageSize = 20,
}: BooksGridProps) {
  const { books, isLoading, error, total } = useBooks({
    enabled: true,
    search: searchQuery,
    sort_by: sortBy,
    sort_order: sortOrder,
    page_size: pageSize,
  });

  if (error) {
    return (
      <div className={styles.errorContainer}>
        <p className={styles.errorMessage}>Error loading books: {error}</p>
      </div>
    );
  }

  if (isLoading && books.length === 0) {
    return (
      <div className={styles.loadingContainer}>
        <p className={styles.loadingMessage}>Loading books...</p>
      </div>
    );
  }

  if (books.length === 0) {
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
          Showing {books.length} of {total} books
        </div>
      )}
      <div className={styles.grid}>
        {books.map((book) => (
          <BookCard
            key={book.id}
            book={book}
            allBooks={books}
            onClick={onBookClick}
          />
        ))}
      </div>
    </div>
  );
}
