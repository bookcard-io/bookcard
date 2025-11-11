"use client";

import { useCallback } from "react";
import { BookViewFormats } from "@/components/books/BookViewFormats";
import { BookViewHeader } from "@/components/books/BookViewHeader";
import { BookViewMetadata } from "@/components/books/BookViewMetadata";
import { BookViewModalFooter } from "@/components/books/BookViewModalFooter";
import { DeleteBookConfirmationModal } from "@/components/books/DeleteBookConfirmationModal";
import { Button } from "@/components/forms/Button";
import { useBook } from "@/hooks/useBook";
import { useDeleteConfirmation } from "@/hooks/useDeleteConfirmation";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import { useModal } from "@/hooks/useModal";
import styles from "./BookViewModal.module.scss";

export interface BookViewModalProps {
  /** Book ID to display. */
  bookId: number | null;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when navigating to previous book. */
  onNavigatePrevious?: () => void;
  /** Callback when navigating to next book. */
  onNavigateNext?: () => void;
  /** Callback when edit button is clicked. Should open edit modal and close view modal. */
  onEdit?: (bookId: number) => void;
}

/**
 * Book view modal component.
 *
 * Displays comprehensive book information in a modal overlay.
 * Users can easily dismiss and navigate between books.
 * Follows SRP by delegating to specialized components.
 * Uses IOC via hooks and components.
 */
export function BookViewModal({
  bookId,
  onClose,
  onNavigatePrevious,
  onNavigateNext,
  onEdit,
}: BookViewModalProps) {
  const { book, isLoading, error } = useBook({
    bookId: bookId || 0,
    enabled: bookId !== null,
    full: true,
  });

  const deleteConfirmation = useDeleteConfirmation({
    onConfirm: () => {
      // TODO: Implement delete functionality
    },
  });

  const handleEdit = useCallback(() => {
    if (bookId && onEdit) {
      onEdit(bookId);
      onClose();
    }
  }, [bookId, onEdit, onClose]);

  const handleDelete = useCallback(() => {
    deleteConfirmation.open();
  }, [deleteConfirmation]);

  // Handle keyboard navigation
  useKeyboardNavigation({
    onEscape: onClose,
    onArrowLeft: onNavigatePrevious,
    onArrowRight: onNavigateNext,
    enabled: !isLoading && !!book && bookId !== null,
  });

  // Prevent body scroll when modal is open
  useModal(bookId !== null);

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose],
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

  if (!bookId) {
    return null;
  }

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
            <Button onClick={onClose} variant="secondary" size="medium">
              Close
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */}
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
            onClick={onClose}
            className={styles.closeButton}
            aria-label="Close"
          >
            ×
          </button>

          <div className={styles.content}>
            <BookViewHeader
              book={book}
              showDescription={true}
              onEdit={handleEdit}
            />

            <div className={styles.mainContent}>
              <BookViewMetadata book={book} />

              {book.formats && book.formats.length > 0 && bookId && (
                <BookViewFormats formats={book.formats} bookId={bookId} />
              )}
            </div>
          </div>

          <BookViewModalFooter onDelete={handleDelete} />
        </div>
      </div>
      {/* Render delete confirmation modal via portal, independent of BookViewModal */}
      {bookId !== null && (
        <DeleteBookConfirmationModal
          isOpen={deleteConfirmation.isOpen}
          dontShowAgain={deleteConfirmation.dontShowAgain}
          deleteFilesFromDrive={deleteConfirmation.deleteFilesFromDrive}
          onClose={deleteConfirmation.close}
          onToggleDontShowAgain={deleteConfirmation.toggleDontShowAgain}
          onToggleDeleteFilesFromDrive={
            deleteConfirmation.toggleDeleteFilesFromDrive
          }
          onConfirm={deleteConfirmation.confirm}
          bookTitle={book?.title}
        />
      )}
    </>
  );
}
