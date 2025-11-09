"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import type { Book } from "@/types/book";
import styles from "./BookCard.module.scss";

export interface BookCardProps {
  /** Book data to display. */
  book: Book;
  /** All books in the grid (needed for range selection). */
  allBooks: Book[];
  /** Callback fired when card is clicked. Reserved for future use. */
  onClick?: (book: Book) => void;
}

/**
 * Book card component for displaying a single book in the grid.
 *
 * Displays book cover thumbnail, title, and author(s).
 * Clicking the card opens the book view modal.
 * Selection is only available via the checkbox overlay.
 * Special overlay buttons (checkbox, edit, menu) stop event propagation.
 * Follows SRP by focusing solely on book display.
 */
export function BookCard({ book, allBooks, onClick: _onClick }: BookCardProps) {
  const { isSelected, handleBookClick } = useSelectedBooks();
  const selected = isSelected(book.id);

  const router = useRouter();

  const handleClick = () => {
    // Open book view modal via callback
    // Special overlay buttons (checkbox, edit, menu) stop propagation
    if (_onClick) {
      _onClick(book);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    // Open book view modal on Enter or Space
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (_onClick) {
        _onClick(book);
      }
    }
  };

  const handleCheckboxClick = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation();
    // Only way to add/remove books from selection is via the checkbox.
    // Create a synthetic event with ctrlKey set to toggle behavior.
    const syntheticEvent = {
      ...e,
      ctrlKey: true,
      metaKey: false,
      shiftKey: false,
    } as React.MouseEvent;
    handleBookClick(book, allBooks, syntheticEvent);
  };

  const handleEditClick = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation();
    router.push(`/books/${book.id}/edit`);
  };

  const authorsText =
    book.authors.length > 0 ? book.authors.join(", ") : "Unknown Author";

  return (
    <button
      type="button"
      className={`${styles.card} ${selected ? styles.selected : ""}`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={`${book.title} by ${authorsText}${selected ? " (selected)" : ""}. Click to view details.`}
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
        <div className={styles.hoverOverlay}>
          {/* biome-ignore lint/a11y/useSemanticElements: Cannot use button inside button, using div with role="button" for accessibility */}
          <div
            className={`${styles.checkbox} ${selected ? styles.checkboxSelected : ""}`}
            onClick={handleCheckboxClick}
            role="button"
            tabIndex={0}
            aria-label={selected ? "Deselect book" : "Select book"}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleCheckboxClick(
                  e as unknown as React.MouseEvent<HTMLDivElement>,
                );
              }
            }}
          >
            {selected && <i className="pi pi-check" aria-hidden="true" />}
          </div>
          {/* biome-ignore lint/a11y/useSemanticElements: Cannot use button inside button, using div with role="button" for accessibility */}
          <div
            className={styles.editButton}
            onClick={handleEditClick}
            role="button"
            tabIndex={0}
            aria-label={`Edit ${book.title}`}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleEditClick(
                  e as unknown as React.MouseEvent<HTMLDivElement>,
                );
              }
            }}
          >
            <i className="pi pi-pencil" aria-hidden="true" />
          </div>
          {/* biome-ignore lint/a11y/useSemanticElements: Cannot use button inside button, using div with role="button" for accessibility */}
          <div
            className={styles.menuButton}
            onClick={(e) => {
              e.stopPropagation();
            }}
            role="button"
            tabIndex={0}
            aria-label="Menu"
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
              }
            }}
          >
            <i className="pi pi-ellipsis-v" aria-hidden="true" />
          </div>
        </div>
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
