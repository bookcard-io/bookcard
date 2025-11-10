"use client";

import { useCallback, useState } from "react";
import { Button } from "@/components/forms/Button";
import { MetadataFetchModal } from "@/components/metadata";
import { useBook } from "@/hooks/useBook";
import { useBookForm } from "@/hooks/useBookForm";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";
import { useModal } from "@/hooks/useModal";
import { useStagedCoverUrl } from "@/hooks/useStagedCoverUrl";
import {
  applyBookUpdateToForm,
  convertMetadataRecordToBookUpdate,
} from "@/utils/metadata";
import { BookEditCoverSection } from "./BookEditCoverSection";
import { BookEditFormFields } from "./BookEditFormFields";
import styles from "./BookEditModal.module.scss";
import { BookEditModalFooter } from "./BookEditModalFooter";
import { BookEditModalHeader } from "./BookEditModalHeader";

export interface BookEditModalProps {
  /** Book ID to edit. */
  bookId: number | null;
  /** Callback when modal should be closed. */
  onClose: () => void;
}

/**
 * Book edit modal component.
 *
 * Displays a comprehensive form for editing book metadata in a modal overlay.
 * Follows SRP by delegating to specialized components.
 * Uses IOC via hooks and components.
 *
 * Parameters
 * ----------
 * props : BookEditModalProps
 *     Component props including book ID and close callback.
 */
export function BookEditModal({ bookId, onClose }: BookEditModalProps) {
  const { book, isLoading, error, updateBook, isUpdating, updateError } =
    useBook({
      bookId: bookId || 0,
      enabled: bookId !== null,
      full: true,
    });

  const { formData, hasChanges, showSuccess, handleFieldChange, handleSubmit } =
    useBookForm({
      book,
      updateBook,
    });

  const [showMetadataModal, setShowMetadataModal] = useState(false);

  const { stagedCoverUrl, setStagedCoverUrl, clearStagedCoverUrl } =
    useStagedCoverUrl({
      bookId,
    });

  /**
   * Handles metadata record selection and populates the form.
   *
   * Parameters
   * ----------
   * record : MetadataRecord
   *     Metadata record from external source.
   */
  const handleSelectMetadata = useCallback(
    (record: MetadataRecord) => {
      const update = convertMetadataRecordToBookUpdate(record);
      applyBookUpdateToForm(update, handleFieldChange);

      // Close the metadata modal after selection
      setShowMetadataModal(false);
    },
    [handleFieldChange],
  );

  const handleClose = useCallback(() => {
    // Reset staged cover URL when closing
    // URL input state is managed internally by BookEditCoverSection
    clearStagedCoverUrl();
    onClose();
  }, [clearStagedCoverUrl, onClose]);

  const handleEscape = useCallback(() => {
    // URL input handles its own Escape key via useCoverUrlInput's handleKeyDown
    // So we can directly close the modal
    handleClose();
  }, [handleClose]);

  // Handle keyboard navigation
  useKeyboardNavigation({
    onEscape: handleEscape,
    enabled: !isLoading && !!book && bookId !== null,
  });

  // Prevent body scroll when modal is open
  useModal(bookId !== null);

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        handleClose();
      }
    },
    [handleClose],
  );

  const handleModalClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      e.stopPropagation();
    },
    [],
  );

  const handleOverlayKeyDown = useCallback(() => {
    // Keyboard navigation is handled by useKeyboardNavigation hook
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

  const authorsText =
    book.authors.length > 0 ? book.authors.join(", ") : "Unknown Author";
  const modalTitle = `Editing book info - ${book.title} by ${authorsText}`;

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
          onFetchMetadata={() => setShowMetadataModal(true)}
        />

        {showMetadataModal && (
          <MetadataFetchModal
            book={book}
            onClose={() => setShowMetadataModal(false)}
            onSelectMetadata={handleSelectMetadata}
          />
        )}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.content}>
            <BookEditCoverSection
              book={book}
              stagedCoverUrl={stagedCoverUrl}
              onCoverUrlSet={setStagedCoverUrl}
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
