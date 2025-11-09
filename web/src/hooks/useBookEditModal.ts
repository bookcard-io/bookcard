import { useCallback, useState } from "react";

export interface UseBookEditModalOptions {
  /** Optional callback when modal is opened. */
  onOpen?: () => void;
  /** Optional callback when modal is closed. */
  onClose?: () => void;
}

export interface UseBookEditModalResult {
  /** Currently editing book ID (null if modal is closed). */
  editingBookId: number | null;
  /** Handler for opening book edit modal. */
  handleEditBook: (bookId: number) => void;
  /** Handler for closing book edit modal. */
  handleCloseModal: () => void;
}

/**
 * Custom hook for managing book edit modal state.
 *
 * Manages the currently editing book ID and modal open/close actions.
 * Follows SRP by managing only book edit modal-related state and logic.
 *
 * Parameters
 * ----------
 * options : UseBookEditModalOptions
 *     Optional configuration including callbacks for open/close events.
 *
 * Returns
 * -------
 * UseBookEditModalResult
 *     Book edit modal state and action handlers.
 */
export function useBookEditModal(
  options: UseBookEditModalOptions = {},
): UseBookEditModalResult {
  const { onOpen, onClose } = options;
  const [editingBookId, setEditingBookId] = useState<number | null>(null);

  const handleEditBook = useCallback(
    (bookId: number) => {
      setEditingBookId(bookId);
      onOpen?.();
    },
    [onOpen],
  );

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
