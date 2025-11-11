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
