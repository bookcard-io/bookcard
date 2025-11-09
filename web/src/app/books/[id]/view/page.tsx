"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { BookViewFormats } from "@/components/books/BookViewFormats";
import { BookViewHeader } from "@/components/books/BookViewHeader";
import { BookViewMetadata } from "@/components/books/BookViewMetadata";
import { Button } from "@/components/forms/Button";
import { useBook } from "@/hooks/useBook";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import { useModal } from "@/hooks/useModal";
import styles from "./page.module.scss";

interface BookViewPageProps {
  params: Promise<{ id: string }>;
}

/**
 * Book view page - large modal for browsing book details.
 *
 * Displays comprehensive book information in a modal format.
 * Users can easily dismiss and navigate between books.
 * Follows SRP by delegating to specialized components.
 * Uses IOC via hooks and components.
 */
export default function BookViewPage({ params }: BookViewPageProps) {
  const router = useRouter();
  const [bookId, setBookId] = useState<number | null>(null);
  const { book, isLoading, error } = useBook({
    bookId: bookId || 0,
    enabled: bookId !== null,
    full: true,
  });

  // Initialize book ID from params
  useEffect(() => {
    void params.then((p) => {
      const id = parseInt(p.id, 10);
      if (!Number.isNaN(id)) {
        setBookId(id);
      }
    });
  }, [params]);

  const handleDismiss = useCallback(() => {
    router.back();
  }, [router]);

  const handleEdit = useCallback(() => {
    if (bookId) {
      router.push(`/books/${bookId}/edit`);
    }
  }, [bookId, router]);

  const handleNavigatePrevious = useCallback(() => {
    if (bookId) {
      router.push(`/books/${bookId - 1}/view`);
    }
  }, [bookId, router]);

  const handleNavigateNext = useCallback(() => {
    if (bookId) {
      router.push(`/books/${bookId + 1}/view`);
    }
  }, [bookId, router]);

  // Handle keyboard navigation
  useKeyboardNavigation({
    onEscape: handleDismiss,
    onArrowLeft: handleNavigatePrevious,
    onArrowRight: handleNavigateNext,
    enabled: !isLoading && !!book,
  });

  // Prevent body scroll when modal is open
  useModal(!isLoading && !!book);

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        handleDismiss();
      }
    },
    [handleDismiss],
  );

  const handleModalClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      e.stopPropagation();
    },
    [],
  );

  const handleOverlayKeyDown = useCallback(() => {
    // Keyboard navigation is handled by useKeyboardNavigation hook
    // This handler exists only to satisfy accessibility requirements
  }, []);

  if (isLoading) {
    return (
      /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
      <div
        className={styles.modalOverlay}
        onClick={handleOverlayClick}
        onKeyDown={handleOverlayKeyDown}
        role="presentation"
      >
        <div
          className={styles.modal}
          role="dialog"
          aria-modal="true"
          aria-label="Book details"
          onMouseDown={handleModalClick}
        >
          <div className={styles.loading}>Loading book data...</div>
        </div>
      </div>
    );
  }

  if (error || !book) {
    return (
      /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
      <div
        className={styles.modalOverlay}
        onClick={handleOverlayClick}
        onKeyDown={handleOverlayKeyDown}
        role="presentation"
      >
        <div
          className={styles.modal}
          role="dialog"
          aria-modal="true"
          aria-label="Book details"
          onMouseDown={handleModalClick}
        >
          <div className={styles.error}>
            {error || "Book not found"}
            <Button onClick={handleDismiss} variant="secondary" size="medium">
              Close
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className={styles.modalOverlay}
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-label="Book details"
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={handleDismiss}
          className={styles.closeButton}
          aria-label="Close"
        >
          ×
        </button>

        <div className={styles.content}>
          <BookViewHeader book={book} />

          <div className={styles.mainContent}>
            {book.description && (
              <section className={styles.section}>
                <h2 className={styles.sectionTitle}>Description</h2>
                <div
                  className={styles.description}
                  // biome-ignore lint/security/noDangerouslySetInnerHtml: Book descriptions from Calibre are trusted HTML content
                  dangerouslySetInnerHTML={{ __html: book.description }}
                />
              </section>
            )}

            <BookViewMetadata book={book} />

            {book.formats && book.formats.length > 0 && (
              <BookViewFormats formats={book.formats} />
            )}
          </div>

          {/* Actions */}
          <div className={styles.actions}>
            <Button
              type="button"
              variant="primary"
              size="medium"
              onClick={handleEdit}
            >
              Edit Metadata
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
