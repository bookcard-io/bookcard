import { useCallback, useRef, useState } from "react";

export interface UseBookCardMenuResult {
  /** Whether the menu is open. */
  isMenuOpen: boolean;
  /** Reference to the menu button element. */
  menuButtonRef: React.RefObject<HTMLDivElement | null>;
  /** Handler for toggling the menu. */
  handleMenuToggle: (e: React.MouseEvent<HTMLDivElement>) => void;
  /** Handler for closing the menu. */
  handleMenuClose: () => void;
}

/**
 * Custom hook for managing book card menu state.
 *
 * Handles menu open/close state and provides handlers.
 * Follows SRP by managing only menu-related state.
 * Uses IOC by returning handlers for parent to use.
 *
 * Returns
 * -------
 * UseBookCardMenuResult
 *     Menu state and handlers.
 */
export function useBookCardMenu(): UseBookCardMenuResult {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuButtonRef = useRef<HTMLDivElement | null>(null);

  const handleMenuToggle = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      e.stopPropagation();
      setIsMenuOpen((prev) => !prev);
    },
    [],
  );

  const handleMenuClose = useCallback(() => {
    setIsMenuOpen(false);
  }, []);

  return {
    isMenuOpen,
    menuButtonRef,
    handleMenuToggle,
    handleMenuClose,
  };
}
