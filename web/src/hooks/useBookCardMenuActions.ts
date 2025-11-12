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

import { useCallback } from "react";
import type { Book } from "@/types/book";
import { useDeleteConfirmation } from "./useDeleteConfirmation";

export interface UseBookCardMenuActionsOptions {
  /** Book data. */
  book: Book;
  /** Callback for opening book view. */
  onBookClick?: (book: Book) => void;
  /** Callback when book is deleted successfully. */
  onBookDeleted?: () => void;
  /** Callback when book deletion fails. */
  onDeleteError?: (error: string) => void;
}

export interface UseBookCardMenuActionsResult {
  /** Handler for Book info action. */
  handleBookInfo: () => void;
  /** Handler for Send action. */
  handleSend: () => void;
  /** Handler for Move to library action. */
  handleMoveToLibrary: () => void;
  /** Handler for Move to shelf action. */
  handleMoveToShelf: () => void;
  /** Handler for Convert action. */
  handleConvert: () => void;
  /** Handler for Delete action. */
  handleDelete: () => void;
  /** Handler for More action. */
  handleMore: () => void;
  /** Delete confirmation modal state and controls. */
  deleteConfirmation: ReturnType<typeof useDeleteConfirmation>;
}

/**
 * Custom hook for book card menu actions.
 *
 * Provides handlers for all menu actions.
 * Follows SRP by managing only menu action handlers.
 * Uses IOC via callback props.
 *
 * Parameters
 * ----------
 * options : UseBookCardMenuActionsOptions
 *     Configuration including book data and callbacks.
 *
 * Returns
 * -------
 * UseBookCardMenuActionsResult
 *     Menu action handlers.
 */
export function useBookCardMenuActions({
  book,
  onBookClick,
  onBookDeleted,
  onDeleteError,
}: UseBookCardMenuActionsOptions): UseBookCardMenuActionsResult {
  const deleteConfirmation = useDeleteConfirmation({
    bookId: book.id,
    onSuccess: () => {
      // Refresh book list or navigate away
      onBookDeleted?.();
    },
    onError: (error) => {
      onDeleteError?.(error);
    },
  });

  const handleBookInfo = useCallback(() => {
    if (onBookClick) {
      onBookClick(book);
    }
  }, [onBookClick, book]);

  const handleSend = useCallback(() => {
    // TODO: Implement send functionality
  }, []);

  const handleMoveToLibrary = useCallback(() => {
    // TODO: Implement move to library functionality
  }, []);

  const handleMoveToShelf = useCallback(() => {
    // TODO: Implement add to shelf functionality
  }, []);

  const handleConvert = useCallback(() => {
    // TODO: Implement convert functionality
  }, []);

  const handleDelete = useCallback(() => {
    deleteConfirmation.open();
  }, [deleteConfirmation]);

  const handleMore = useCallback(() => {
    // TODO: Implement more options functionality
  }, []);

  return {
    handleBookInfo,
    handleSend,
    handleMoveToLibrary,
    handleMoveToShelf,
    handleConvert,
    handleDelete,
    handleMore,
    deleteConfirmation,
  };
}
