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
import { TrackedBookEditCoverSection } from "@/components/tracked-books/detail/TrackedBookEditCoverSection";
import { TrackedBookEditFormFields } from "@/components/tracked-books/detail/TrackedBookEditFormFields";
import { TrackedBookEditModalFooter } from "@/components/tracked-books/detail/TrackedBookEditModalFooter";
import { useModal } from "@/hooks/useModal";
import { useTrackedBookEditForm } from "@/hooks/useTrackedBookEditForm";
import type { TrackedBook } from "@/types/trackedBook";

export interface TrackedBookEditModalProps {
  /** Tracked book to edit. */
  book: TrackedBook;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when tracked book is saved. */
  onBookSaved?: (book: TrackedBook) => void;
}

/**
 * Tracked book edit modal component.
 *
 * Mirrors the `BookEditModal` patterns (form + validation + footer messages),
 * but intentionally does not include metadata fetching wiring.
 *
 * Parameters
 * ----------
 * props : TrackedBookEditModalProps
 *     Component props including tracked book and callbacks.
 */
export function TrackedBookEditModal({
  book,
  onClose,
  onBookSaved,
}: TrackedBookEditModalProps) {
  const {
    form,
    hasChanges,
    showSuccess,
    isUpdating,
    updateError,
    handleFieldChange,
    handleSubmit,
    handleClose,
  } = useTrackedBookEditForm({
    book,
    onClose,
    onBookSaved,
  });

  useModal(true);

  const formTitle = useWatch({
    control: form.control,
    name: "title",
  });

  const coverUrl = useWatch({
    control: form.control,
    name: "cover_url",
  });

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
    // Keyboard navigation handled by hook
  }, []);

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
        aria-label={`Editing tracked book ${formTitle || book.title}`}
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

        <div className="modal-header">
          <div className="flex min-w-0 flex-1 flex-col gap-1">
            <h2 className="m-0 hidden truncate font-bold text-2xl text-text-a0 leading-[1.4] md:block">
              Editing {formTitle || book.title || "Untitled"}
            </h2>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col">
          <div className="grid min-h-0 flex-1 grid-cols-1 gap-6 overflow-y-auto p-6 lg:[grid-template-columns:250px_1fr]">
            <TrackedBookEditCoverSection
              book={book}
              coverUrl={coverUrl}
              onCoverUrlSet={(url) => handleFieldChange("cover_url", url)}
              isUpdating={isUpdating}
            />
            <TrackedBookEditFormFields form={form} />
          </div>

          <TrackedBookEditModalFooter
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
