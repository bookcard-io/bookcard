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
  const { book, isLoading, error } = useBook({
    bookId: bookId || 0,
    enabled: bookId !== null,
    full: true,
  });

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
      // Error is displayed in the modal via deleteConfirmation.error
      console.error("Failed to delete book:", error);
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
        className="fixed inset-0 z-[1000] flex animate-[fadeIn_0.2s_ease-out] items-center justify-center overflow-y-auto bg-black/70 p-4 md:p-2"
        onClick={handleOverlayClick}
        onKeyDown={handleOverlayKeyDown}
        role="presentation"
      >
        <div
          className="relative flex max-h-[90vh] min-h-[90vh] w-full max-w-[900px] animate-[slideUp_0.3s_ease-out] flex-col overflow-y-auto rounded-2xl bg-[var(--color-surface-a10)] shadow-[0_20px_60px_rgba(0,0,0,0.5)] md:max-h-[98vh] md:rounded-xl"
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
        className="fixed inset-0 z-[1000] flex animate-[fadeIn_0.2s_ease-out] items-center justify-center overflow-y-auto bg-black/70 p-4 md:p-2"
        onClick={handleOverlayClick}
        onKeyDown={handleOverlayKeyDown}
        role="presentation"
      >
        <div
          className="relative flex max-h-[90vh] min-h-[90vh] w-full max-w-[900px] animate-[slideUp_0.3s_ease-out] flex-col overflow-y-auto rounded-2xl bg-[var(--color-surface-a10)] shadow-[0_20px_60px_rgba(0,0,0,0.5)] md:max-h-[98vh] md:rounded-xl"
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
        className="fixed inset-0 z-[1000] flex animate-[fadeIn_0.2s_ease-out] items-center justify-center overflow-y-auto bg-black/70 p-4 md:p-2"
        onClick={handleOverlayClick}
        onKeyDown={handleOverlayKeyDown}
        role="presentation"
      >
        <div
          className="relative flex max-h-[90vh] min-h-[90vh] w-full max-w-[900px] animate-[slideUp_0.3s_ease-out] flex-col overflow-y-auto rounded-2xl bg-[var(--color-surface-a10)] shadow-[0_20px_60px_rgba(0,0,0,0.5)] md:max-h-[98vh] md:rounded-xl"
          role="dialog"
          aria-modal="true"
          aria-label="Book details"
          onMouseDown={handleModalClick}
        >
          <button
            type="button"
            onClick={onClose}
            className="absolute top-4 right-4 z-10 flex h-10 w-10 items-center justify-center rounded-full border-none bg-transparent p-2 text-[2rem] text-[var(--color-text-a30)] leading-none transition-all duration-200 hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a0)] focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2"
            aria-label="Close"
          >
            ×
          </button>

          <div className="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto p-6 md:gap-4 md:p-4">
            <BookViewHeader
              book={book}
              showDescription={true}
              onEdit={handleEdit}
            />

            <div className="flex flex-col gap-5 md:gap-4">
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
          isDeleting={deleteConfirmation.isDeleting}
          error={deleteConfirmation.error}
        />
      )}
    </>
  );
}
