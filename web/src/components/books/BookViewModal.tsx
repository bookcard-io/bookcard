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
import { BookViewFormats } from "@/components/books/BookViewFormats";
import { BookViewHeader } from "@/components/books/BookViewHeader";
import { BookViewMetadata } from "@/components/books/BookViewMetadata";
import { BookViewModalFooter } from "@/components/books/BookViewModalFooter";
import { DeleteBookConfirmationModal } from "@/components/books/DeleteBookConfirmationModal";
import { Button } from "@/components/forms/Button";
import { BookReadingInfo } from "@/components/reading/BookReadingInfo";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useBook } from "@/hooks/useBook";
import { useDeleteConfirmation } from "@/hooks/useDeleteConfirmation";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import { useModal } from "@/hooks/useModal";

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
  /** Callback when book is deleted. */
  onBookDeleted?: (bookId: number) => void;
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
  onBookDeleted,
}: BookViewModalProps) {
  const { showDanger } = useGlobalMessages();
  const { book, isLoading, error } = useBook({
    bookId: bookId || 0,
    enabled: bookId !== null,
    full: true,
  });

  const modalContainerClassName =
    "modal-container modal-container-shadow-large max-h-[90vh] min-h-[90vh] w-full max-w-[900px] md:max-h-[98vh] md:rounded-md";

  const deleteConfirmation = useDeleteConfirmation({
    bookId: bookId || null,
    onSuccess: () => {
      // Notify parent that book was deleted
      if (bookId !== null) {
        onBookDeleted?.(bookId);
      }
      // Close modal
      onClose();
    },
    onError: (error) => {
      showDanger(error);
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
        className="modal-overlay modal-overlay-z-1000 modal-overlay-padding-responsive"
        onClick={handleOverlayClick}
        onKeyDown={handleOverlayKeyDown}
        role="presentation"
      >
        <div
          className={modalContainerClassName}
          role="dialog"
          aria-modal="true"
          aria-label="Book details"
          onMouseDown={handleModalClick}
        >
          <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-[var(--color-text-a30)]">
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
        className="modal-overlay modal-overlay-z-1000 modal-overlay-padding-responsive"
        onClick={handleOverlayClick}
        onKeyDown={handleOverlayKeyDown}
        role="presentation"
      >
        <div
          className={modalContainerClassName}
          role="dialog"
          aria-modal="true"
          aria-label="Book details"
          onMouseDown={handleModalClick}
        >
          <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-[var(--color-text-a30)]">
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
        className="modal-overlay modal-overlay-z-1000 modal-overlay-padding-responsive"
        onClick={handleOverlayClick}
        onKeyDown={handleOverlayKeyDown}
        role="presentation"
      >
        <div
          className={modalContainerClassName}
          role="dialog"
          aria-modal="true"
          aria-label="Book details"
          onMouseDown={handleModalClick}
        >
          <button
            type="button"
            onClick={onClose}
            className="modal-close-button modal-close-button-sm transition-all hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a0)]"
            aria-label="Close"
          >
            <i className="pi pi-times" aria-hidden="true" />
          </button>

          <div className="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto p-6 md:gap-4 md:p-4">
            <BookViewHeader
              book={book}
              showDescription={true}
              onEdit={handleEdit}
            />

            <div className="flex flex-col gap-5 md:gap-4">
              <BookViewMetadata book={book} />

              {book && <BookReadingInfo book={book} />}

              {book.formats && book.formats.length > 0 && bookId && (
                <BookViewFormats formats={book.formats} book={book} />
              )}
            </div>
          </div>

          <BookViewModalFooter onDelete={handleDelete} book={book} />
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
          book={book}
          isDeleting={deleteConfirmation.isDeleting}
          error={deleteConfirmation.error}
        />
      )}
    </>
  );
}
