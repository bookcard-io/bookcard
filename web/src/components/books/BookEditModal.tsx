// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

"use client";

import { useCallback } from "react";
import { useWatch } from "react-hook-form";
import { Button } from "@/components/forms/Button";
import { MetadataFetchModal } from "@/components/metadata";
import { useBookEditForm } from "@/hooks/useBookEditForm";
import { useModal } from "@/hooks/useModal";
import type { Book } from "@/types/book";
import { getBookEditModalTitle } from "@/utils/books";
import { BookEditCoverSection } from "./BookEditCoverSection";
import { BookEditFormFields } from "./BookEditFormFields";
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
    form,
    hasChanges,
    showSuccess,
    isUpdating,
    updateError,
    stagedCoverUrl,
    showMetadataModal,
    isLuckySearching,
    handleFieldChange,
    handleSubmit,
    handleClose,
    handleOpenMetadataModal,
    handleCloseMetadataModal,
    handleSelectMetadata,
    handleFeelinLucky,
    handleCoverSaved,
  } = useBookEditForm({
    bookId,
    onClose,
    onCoverSaved,
    onBookSaved,
  });

  // Prevent body scroll when modal is open
  useModal(bookId !== null);

  // Watch title field for reactive updates to modal title
  // Must be called before any early returns to follow Rules of Hooks
  const formTitle = useWatch({
    control: form.control,
    name: "title",
  });

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
        className="modal-overlay modal-overlay-z-1000 modal-overlay-padding"
        onClick={handleOverlayClick}
        onKeyDown={handleOverlayKeyDown}
        role="presentation"
      >
        <div
          className="modal-container modal-container-shadow-default max-h-[90vh] min-h-[90vh] w-full max-w-[90vw]"
          role="dialog"
          aria-modal="true"
          aria-label="Editing book info"
          onMouseDown={handleModalClick}
        >
          <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-base text-text-a30">
            Loading book data...
          </div>
        </div>
      </div>
    );
  }

  if (error || !book) {
    return (
      /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
      <div
        className="modal-overlay modal-overlay-z-1000 modal-overlay-padding"
        onClick={handleOverlayClick}
        onKeyDown={handleOverlayKeyDown}
        role="presentation"
      >
        <div
          className="modal-container modal-container-shadow-default max-h-[90vh] min-h-[90vh] w-full max-w-[90vw]"
          role="dialog"
          aria-modal="true"
          aria-label="Editing book info"
          onMouseDown={handleModalClick}
        >
          <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-base text-text-a30">
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
    ? getBookEditModalTitle(book, formTitle ?? undefined)
    : "Editing book info";

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-1000 modal-overlay-padding"
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className="modal-container modal-container-shadow-default max-h-[90vh] min-h-[90vh] w-full max-w-[90vw]"
        role="dialog"
        aria-modal="true"
        aria-label={modalTitle}
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={handleClose}
          className="modal-close-button modal-close-button-sm focus:outline"
          aria-label="Close"
        >
          <i className="pi pi-times" aria-hidden="true" />
        </button>

        <BookEditModalHeader
          book={book}
          formTitle={formTitle || undefined}
          isUpdating={isUpdating}
          isLuckySearching={isLuckySearching}
          onFetchMetadata={handleOpenMetadataModal}
          onFeelinLucky={handleFeelinLucky}
        />

        {showMetadataModal && (
          <MetadataFetchModal
            book={book}
            formData={form.getValues()}
            onClose={handleCloseMetadataModal}
            onSelectMetadata={handleSelectMetadata}
          />
        )}

        <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col">
          <div className="grid min-h-0 flex-1 grid-cols-1 gap-6 overflow-y-auto p-6 lg:[grid-template-columns:250px_1fr]">
            <BookEditCoverSection
              book={book}
              stagedCoverUrl={stagedCoverUrl}
              onCoverSaved={handleCoverSaved}
            />
            <BookEditFormFields book={book} form={form} />
          </div>

          <BookEditModalFooter
            book={book}
            updateError={updateError}
            formErrors={form.formState.errors}
            showSuccess={showSuccess}
            isUpdating={isUpdating}
            hasChanges={hasChanges}
            onCancel={handleClose}
            handleFieldChange={handleFieldChange}
          />
        </form>
      </div>
    </div>
  );
}
