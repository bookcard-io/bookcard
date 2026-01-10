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

import { useCallback, useRef, useState } from "react";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import { useTrackedBookForm } from "@/hooks/useTrackedBookForm";
import { trackedBookService } from "@/services/trackedBookService";
import type { TrackedBook, TrackedBookUpdate } from "@/types/trackedBook";

export interface UseTrackedBookEditFormOptions {
  /** Tracked book to edit. */
  book: TrackedBook | null;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when tracked book is saved. */
  onBookSaved?: (book: TrackedBook) => void;
}

export interface UseTrackedBookEditFormResult {
  /** Current tracked book. */
  book: TrackedBook | null;
  /** React Hook Form instance. */
  form: ReturnType<typeof useTrackedBookForm>["form"];
  /** Whether form has unsaved changes. */
  hasChanges: boolean;
  /** Whether update was successful. */
  showSuccess: boolean;
  /** Whether update is in progress. */
  isUpdating: boolean;
  /** Error message if update failed. */
  updateError: string | null;
  /** Handler for field changes. */
  handleFieldChange: ReturnType<typeof useTrackedBookForm>["handleFieldChange"];
  /** Handler for form submission. */
  handleSubmit: ReturnType<typeof useTrackedBookForm>["handleSubmit"];
  /** Handler for closing the modal (with cleanup). */
  handleClose: () => void;
}

/**
 * Custom hook for managing tracked book edit form business logic.
 *
 * Mirrors the overall `useBookEditForm` shape but intentionally excludes
 * metadata-fetch wiring for tracked books.
 *
 * Parameters
 * ----------
 * options : UseTrackedBookEditFormOptions
 *     Configuration including tracked book and callbacks.
 *
 * Returns
 * -------
 * UseTrackedBookEditFormResult
 *     Form state and handlers needed for the modal UI.
 */
export function useTrackedBookEditForm({
  book,
  onClose,
  onBookSaved,
}: UseTrackedBookEditFormOptions): UseTrackedBookEditFormResult {
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  const handleCloseRef = useRef<(() => void) | null>(null);

  const updateBook = useCallback(
    async (update: TrackedBookUpdate) => {
      if (!book?.id) {
        return null;
      }
      setIsUpdating(true);
      setUpdateError(null);
      try {
        const updated = await trackedBookService.update(book.id, update);
        return updated;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to update tracked book";
        setUpdateError(message);
        return null;
      } finally {
        setIsUpdating(false);
      }
    },
    [book?.id, book],
  );

  const {
    form,
    hasChanges,
    showSuccess,
    handleFieldChange,
    handleSubmit: handleFormSubmit,
    resetForm,
  } = useTrackedBookForm({
    book,
    updateBook,
    onUpdateSuccess: (updatedBook) => {
      onBookSaved?.(updatedBook);
    },
  });

  const handleClose = useCallback(() => {
    resetForm();
    onClose();
  }, [resetForm, onClose]);

  handleCloseRef.current = handleClose;

  const handleEscape = useCallback(() => {
    handleCloseRef.current?.();
  }, []);

  useKeyboardNavigation({
    onEscape: handleEscape,
    enabled: !!book,
  });

  const handleSubmit = useCallback(
    async (e: React.FormEvent): Promise<boolean> => {
      const success = await handleFormSubmit(e);
      if (success) {
        // Keep modal open; users can close manually (consistent with edit patterns)
      }
      return success;
    },
    [handleFormSubmit],
  );

  return {
    book,
    form,
    hasChanges,
    showSuccess,
    isUpdating,
    updateError,
    handleFieldChange,
    handleSubmit,
    handleClose,
  };
}
