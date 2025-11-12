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

import { useCallback, useState } from "react";

export interface UseBookEditModalOptions {
  /** Callback when modal is opened. */
  onOpen?: () => void;
  /** Callback when modal is closed. */
  onClose?: () => void;
}

export interface UseBookEditModalResult {
  /** Currently editing book ID (null if modal is closed). */
  editingBookId: number | null;
  /** Handler for opening edit modal with a book ID. */
  handleEditBook: (bookId: number) => void;
  /** Handler for closing the edit modal. */
  handleCloseModal: () => void;
}

/**
 * Custom hook for managing book edit modal state.
 *
 * Manages the currently editing book ID and modal open/close actions.
 * Follows SRP by managing only modal state and lifecycle.
 * Uses IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UseBookEditModalOptions
 *     Optional configuration including callbacks.
 *
 * Returns
 * -------
 * UseBookEditModalResult
 *     Modal state and action handlers.
 */
export function useBookEditModal(
  options: UseBookEditModalOptions = {},
): UseBookEditModalResult {
  const { onOpen, onClose } = options;
  const [editingBookId, setEditingBookId] = useState<number | null>(null);

  /**
   * Handles opening the edit modal for a specific book.
   *
   * Parameters
   * ----------
   * bookId : number
   *     Book ID to edit.
   */
  const handleEditBook = useCallback(
    (bookId: number) => {
      setEditingBookId(bookId);
      onOpen?.();
    },
    [onOpen],
  );

  /**
   * Handles closing the edit modal.
   */
  const handleCloseModal = useCallback(() => {
    setEditingBookId(null);
    onClose?.();
  }, [onClose]);

  return {
    editingBookId,
    handleEditBook,
    handleCloseModal,
  };
}
