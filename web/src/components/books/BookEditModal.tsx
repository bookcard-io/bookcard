"use client";

import { useCallback } from "react";
import { Button } from "@/components/forms/Button";
import { MetadataFetchModal } from "@/components/metadata";
import { useBookEditForm } from "@/hooks/useBookEditForm";
import { useModal } from "@/hooks/useModal";
import type { Book } from "@/types/book";
import { getBookEditModalTitle } from "@/utils/books";
import { BookEditCoverSection } from "./BookEditCoverSection";
import { BookEditFormFields } from "./BookEditFormFields";
import styles from "./BookEditModal.module.scss";
import { BookEditModalFooter } from "./BookEditModalFooter";
import { BookEditModalHeader } from "./BookEditModalHeader";

export interface BookEditModalProps {
  /** Book ID to edit. */
  bookId: number;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when cover is saved (for updating grid). */
  onCoverSaved?: (bookId: number) => void;
  /** Callback when book is saved (for updating grid). */
  onBookSaved?: (book: Book) => void;
}

/**
 * Book edit modal component.
 *
 * Displays a comprehensive form for editing book metadata in a modal overlay.
 * Follows SRP by delegating form logic to useBookEditForm hook.
 * Uses IOC via hooks and components. Focused solely on UI rendering.
 *
 * Parameters
 * ----------
 * props : BookEditModalProps
 *     Component props including book ID and callbacks.
 */
export function BookEditModal({
  bookId,
  onClose,
  onCoverSaved,
  onBookSaved,
}: BookEditModalProps) {
  const {
    book,
    isLoading,
    error,
    formData,
    hasChanges,
    showSuccess,
    isUpdating,
    updateError,
    stagedCoverUrl,
    showMetadataModal,
    handleFieldChange,
    handleSubmit,
    handleClose,
    handleOpenMetadataModal,
    handleCloseMetadataModal,
    handleSelectMetadata,
    handleCoverSaved,
  } = useBookEditForm({
    bookId,
    onClose,
    onCoverSaved,
    onBookSaved,
  });

  // Prevent body scroll when modal is open
  useModal(bookId !== null);

  /**
   * Handles overlay click to close modal.
   */
  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        handleClose();
      }
    },
    [handleClose],
  );

  /**
   * Prevents modal content clicks from closing the modal.
   */
  const handleModalClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      e.stopPropagation();
    },
    [],
  );

  /**
   * Placeholder for overlay keydown (keyboard navigation handled by hook).
   */
  const handleOverlayKeyDown = useCallback(() => {
    // Keyboard navigation is handled by useBookEditForm hook
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
          aria-label="Editing book info"
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
          aria-label="Editing book info"
          onMouseDown={handleModalClick}
        >
          <div className={styles.error}>
            {error || "Book not found"}
            <Button onClick={handleClose} variant="secondary" size="medium">
              Close
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const modalTitle = book
    ? getBookEditModalTitle(book, formData.title)
    : "Editing book info";

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
        aria-label={modalTitle}
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={handleClose}
          className={styles.closeButton}
          aria-label="Close"
        >
          ×
        </button>

        <BookEditModalHeader
          book={book}
          formTitle={formData.title}
          isUpdating={isUpdating}
          onFetchMetadata={handleOpenMetadataModal}
        />

        {showMetadataModal && (
          <MetadataFetchModal
            book={book}
            formData={formData}
            onClose={handleCloseMetadataModal}
            onSelectMetadata={handleSelectMetadata}
          />
        )}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.content}>
            <BookEditCoverSection
              book={book}
              stagedCoverUrl={stagedCoverUrl}
              onCoverSaved={handleCoverSaved}
            />
            <BookEditFormFields
              book={book}
              formData={formData}
              onFieldChange={handleFieldChange}
            />
          </div>

          <BookEditModalFooter
            updateError={updateError}
            showSuccess={showSuccess}
            isUpdating={isUpdating}
            hasChanges={hasChanges}
            onCancel={handleClose}
          />
        </form>
      </div>
    </div>
  );
}
