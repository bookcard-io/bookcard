"use client";

import Image from "next/image";
import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import type { Book } from "@/types/book";
import styles from "./BookCard.module.scss";

export interface BookCardProps {
  /** Book data to display. */
  book: Book;
  /** All books in the grid (needed for range selection). */
  allBooks: Book[];
  /** Callback fired when card is clicked (for navigation). */
  onClick?: (book: Book) => void;
}

/**
 * Book card component for displaying a single book in the grid.
 *
 * Displays book cover thumbnail, title, and author(s).
 * Supports multi-select with Ctrl/Shift+click.
 * Follows SRP by focusing solely on book display.
 */
export function BookCard({ book, allBooks, onClick }: BookCardProps) {
  const { isSelected, handleBookClick } = useSelectedBooks();
  const selected = isSelected(book.id);

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    // Handle multi-select first
    handleBookClick(book, allBooks, e);
    // Then call optional onClick for navigation
    if (!e.ctrlKey && !e.metaKey && !e.shiftKey) {
      onClick?.(book);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      // For keyboard, just call onClick (no multi-select via keyboard)
      onClick?.(book);
    }
  };

  const authorsText =
    book.authors.length > 0 ? book.authors.join(", ") : "Unknown Author";

  return (
    <button
      type="button"
      className={`${styles.card} ${selected ? styles.selected : ""}`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={`View details for ${book.title} by ${authorsText}${selected ? " (selected)" : ""}`}
      data-book-card
    >
      <div className={styles.coverContainer}>
        {book.thumbnail_url ? (
          <Image
            src={book.thumbnail_url}
            alt={`Cover for ${book.title}`}
            width={200}
            height={300}
            className={styles.cover}
            unoptimized
          />
        ) : (
          <div className={styles.coverPlaceholder}>
            <span className={styles.placeholderText}>No Cover</span>
          </div>
        )}
      </div>
      <div className={styles.info}>
        <h3 className={styles.title} title={book.title}>
          {book.title}
        </h3>
        <p className={styles.author} title={authorsText}>
          {authorsText}
        </p>
      </div>
    </button>
  );
}
