import { useCallback, useState } from "react";

export interface UseBookViewModalResult {
  /** Currently viewing book ID (null if modal is closed). */
  viewingBookId: number | null;
  /** Handler for opening book modal. */
  handleBookClick: (book: { id: number }) => void;
  /** Handler for closing book modal. */
  handleCloseModal: () => void;
  /** Handler for navigating to previous book. */
  handleNavigatePrevious: () => void;
  /** Handler for navigating to next book. */
  handleNavigateNext: () => void;
}

/**
 * Custom hook for managing book view modal state and navigation.
 *
 * Manages the currently viewing book ID and navigation actions.
 * Follows SRP by managing only book modal-related state and logic.
 *
 * Returns
 * -------
 * UseBookViewModalResult
 *     Book modal state and action handlers.
 */
export function useBookViewModal(): UseBookViewModalResult {
  const [viewingBookId, setViewingBookId] = useState<number | null>(null);

  const handleBookClick = useCallback((book: { id: number }) => {
    setViewingBookId(book.id);
  }, []);

  const handleCloseModal = useCallback(() => {
    setViewingBookId(null);
  }, []);

  const handleNavigatePrevious = useCallback(() => {
    if (viewingBookId) {
      setViewingBookId(viewingBookId - 1);
    }
  }, [viewingBookId]);

  const handleNavigateNext = useCallback(() => {
    if (viewingBookId) {
      setViewingBookId(viewingBookId + 1);
    }
  }, [viewingBookId]);

  return {
    viewingBookId,
    handleBookClick,
    handleCloseModal,
    handleNavigatePrevious,
    handleNavigateNext,
  };
}
