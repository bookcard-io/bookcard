import { useCallback, useEffect, useRef, useState } from "react";

export interface UseBookViewModalOptions {
  /** Optional list of book IDs to navigate within. */
  bookIds?: number[];
  /** Function to load more books (for infinite scroll). */
  loadMore?: () => void;
  /** Whether there are more books to load. */
  hasMore?: boolean;
  /** Whether books are currently being loaded. */
  isLoading?: boolean;
  /** Number of books from end to trigger preloading (default: 3). */
  preloadThreshold?: number;
}

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
 * Navigation uses the provided bookIds array to find the previous/next book,
 * preventing navigation to non-existent books.
 * Supports infinite keyboard browsing by automatically loading more books
 * when navigating near boundaries.
 * Follows SRP by managing only book modal-related state and logic.
 *
 * Parameters
 * ----------
 * options : UseBookViewModalOptions
 *     Optional configuration including list of book IDs for navigation
 *     and callbacks for infinite scroll support.
 *
 * Returns
 * -------
 * UseBookViewModalResult
 *     Book modal state and action handlers.
 */
export function useBookViewModal(
  options: UseBookViewModalOptions = {},
): UseBookViewModalResult {
  const {
    bookIds,
    loadMore,
    hasMore,
    isLoading,
    preloadThreshold = 3,
  } = options;
  const [viewingBookId, setViewingBookId] = useState<number | null>(null);
  const pendingNavigationRef = useRef<"next" | "previous" | null>(null);
  const previousBookIdsLengthRef = useRef<number>(0);

  // Handle automatic navigation after books are loaded
  useEffect(() => {
    if (
      pendingNavigationRef.current &&
      bookIds &&
      bookIds.length > previousBookIdsLengthRef.current
    ) {
      // Books were loaded, now navigate
      const currentIndex = bookIds.indexOf(viewingBookId || -1);
      if (currentIndex >= 0) {
        if (pendingNavigationRef.current === "next") {
          const nextIndex = currentIndex + 1;
          if (nextIndex < bookIds.length) {
            const nextId = bookIds[nextIndex];
            if (nextId !== undefined) {
              setViewingBookId(nextId);
            }
          }
        }
        // For previous, we don't load more books (infinite scroll typically only goes forward)
      }
      pendingNavigationRef.current = null;
    }
    previousBookIdsLengthRef.current = bookIds?.length || 0;
  }, [bookIds, viewingBookId]);

  const handleBookClick = useCallback((book: { id: number }) => {
    setViewingBookId(book.id);
    pendingNavigationRef.current = null;
  }, []);

  const handleCloseModal = useCallback(() => {
    setViewingBookId(null);
    pendingNavigationRef.current = null;
  }, []);

  const handleNavigatePrevious = useCallback(() => {
    if (!viewingBookId) {
      return;
    }

    // If bookIds array is provided, navigate within that list
    if (bookIds && bookIds.length > 0) {
      const currentIndex = bookIds.indexOf(viewingBookId);
      if (currentIndex > 0) {
        // Navigate to previous book in the list
        const prevId = bookIds[currentIndex - 1];
        if (prevId !== undefined) {
          setViewingBookId(prevId);
        }
        pendingNavigationRef.current = null;
      }
      // If at the beginning, do nothing (no navigation)
      return;
    }

    // Fallback: if no bookIds provided, don't navigate
    // This prevents the old buggy behavior of incrementing/decrementing
  }, [viewingBookId, bookIds]);

  // Helper to check if we should preload more books
  const shouldPreload = useCallback(
    (currentIndex: number, totalBooks: number): boolean => {
      const booksFromEnd = totalBooks - (currentIndex + 1);
      return (
        booksFromEnd <= preloadThreshold &&
        Boolean(hasMore && loadMore && !isLoading)
      );
    },
    [preloadThreshold, hasMore, loadMore, isLoading],
  );

  // Helper to check if we can load more books at the end
  const canLoadMore = useCallback((): boolean => {
    return Boolean(hasMore && loadMore && !isLoading);
  }, [hasMore, loadMore, isLoading]);

  const handleNavigateNext = useCallback(() => {
    if (!viewingBookId || !bookIds || bookIds.length === 0) {
      return;
    }

    const currentIndex = bookIds.indexOf(viewingBookId);
    if (currentIndex < 0) {
      return;
    }

    // Check if we can navigate to next book in currently loaded list
    if (currentIndex < bookIds.length - 1) {
      // Navigate to next book in the list
      const nextId = bookIds[currentIndex + 1];
      if (nextId !== undefined) {
        setViewingBookId(nextId);
      }
      pendingNavigationRef.current = null;

      // Preload more books if we're near the end
      if (shouldPreload(currentIndex + 1, bookIds.length)) {
        loadMore?.();
      }
      return;
    }

    // If at the end and there are more books, load them
    if (currentIndex === bookIds.length - 1 && canLoadMore()) {
      pendingNavigationRef.current = "next";
      loadMore?.();
      return;
    }

    // If at the end and no more books, do nothing
  }, [viewingBookId, bookIds, shouldPreload, canLoadMore, loadMore]);

  return {
    viewingBookId,
    handleBookClick,
    handleCloseModal,
    handleNavigatePrevious,
    handleNavigateNext,
  };
}
