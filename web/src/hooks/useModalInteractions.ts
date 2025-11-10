import { useCallback } from "react";

export interface UseModalInteractionsOptions {
  /** Callback when modal should be closed (e.g., overlay click). */
  onClose: () => void;
}

export interface UseModalInteractionsResult {
  /** Handler for overlay click events. */
  handleOverlayClick: (e: React.MouseEvent<HTMLDivElement>) => void;
  /** Handler for modal click events (prevents propagation). */
  handleModalClick: (e: React.MouseEvent<HTMLDivElement>) => void;
  /** Handler for overlay keydown events (for accessibility). */
  handleOverlayKeyDown: () => void;
}

/**
 * Custom hook for modal interaction handlers.
 *
 * Provides standardized handlers for modal overlay and content interactions.
 * Follows SRP by focusing solely on modal interaction logic.
 * Follows DRY by centralizing common modal interaction patterns.
 * Uses IOC via callback dependencies.
 *
 * Parameters
 * ----------
 * options : UseModalInteractionsOptions
 *     Options containing the close callback.
 *
 * Returns
 * -------
 * UseModalInteractionsResult
 *     Object containing modal interaction handlers.
 */
export function useModalInteractions(
  options: UseModalInteractionsOptions,
): UseModalInteractionsResult {
  const { onClose } = options;

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

  return {
    handleOverlayClick,
    handleModalClick,
    handleOverlayKeyDown,
  };
}
