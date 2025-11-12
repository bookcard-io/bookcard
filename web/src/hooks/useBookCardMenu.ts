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
