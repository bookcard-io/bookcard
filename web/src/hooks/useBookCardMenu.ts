import { useCallback, useRef, useState } from "react";

export interface UseBookCardMenuResult {
  /** Whether the menu is open. */
  isMenuOpen: boolean;
  /** Reference to the menu button element. */
  menuButtonRef: React.RefObject<HTMLDivElement | null>;
  /** Cursor position when menu was opened. */
  cursorPosition: { x: number; y: number } | null;
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
  const [cursorPosition, setCursorPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const menuButtonRef = useRef<HTMLDivElement | null>(null);

  const handleMenuToggle = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      e.stopPropagation();
      const wasOpen = isMenuOpen;
      setIsMenuOpen((prev) => !prev);

      // Capture cursor position when opening menu
      if (!wasOpen) {
        setCursorPosition({
          x: e.clientX,
          y: e.clientY,
        });
      } else {
        setCursorPosition(null);
      }
    },
    [isMenuOpen],
  );

  const handleMenuClose = useCallback(() => {
    setIsMenuOpen(false);
    setCursorPosition(null);
  }, []);

  return {
    isMenuOpen,
    menuButtonRef,
    cursorPosition,
    handleMenuToggle,
    handleMenuClose,
  };
}
