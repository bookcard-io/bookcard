import { useCallback } from "react";
import type { Book } from "@/types/book";
import { useDeleteConfirmation } from "./useDeleteConfirmation";

export interface UseBookCardMenuActionsOptions {
  /** Book data. */
  book: Book;
  /** Callback for opening book view. */
  onBookClick?: (book: Book) => void;
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
}: UseBookCardMenuActionsOptions): UseBookCardMenuActionsResult {
  const deleteConfirmation = useDeleteConfirmation({
    onConfirm: () => {
      // TODO: Implement delete functionality
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
