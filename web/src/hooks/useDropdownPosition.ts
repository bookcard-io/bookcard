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

import { useEffect, useRef, useState } from "react";

/** Vertical offset for menu positioning (positive = down). */
const MENU_OFFSET_Y = 2;

/** Horizontal offset for menu positioning (negative = left, positive = right). */
const MENU_OFFSET_X = -2;

export interface UseDropdownPositionOptions {
  /** Whether the menu is open. */
  isOpen: boolean;
  /** Reference to the button element. */
  buttonRef: React.RefObject<HTMLElement | null>;
  /** Cursor position when menu was opened. */
  cursorPosition: { x: number; y: number } | null;
}

export interface UseDropdownPositionResult {
  /** Calculated position for the menu (top and right in pixels). */
  position: { top: number; right: number };
}

/**
 * Custom hook for calculating dropdown menu position.
 *
 * Handles positioning relative to button element while maintaining
 * cursor-relative offset. Updates position on scroll and resize.
 * Follows SRP by handling only position calculation logic.
 * Follows IOC by accepting refs and position data as inputs.
 *
 * Parameters
 * ----------
 * options : UseDropdownPositionOptions
 *     Configuration including open state, button ref, and cursor position.
 *
 * Returns
 * -------
 * UseDropdownPositionResult
 *     Calculated position coordinates.
 */
export function useDropdownPosition({
  isOpen,
  buttonRef,
  cursorPosition,
}: UseDropdownPositionOptions): UseDropdownPositionResult {
  const [position, setPosition] = useState({ top: 0, right: 0 });
  const cursorOffsetRef = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    if (!isOpen || !cursorPosition) {
      cursorOffsetRef.current = null;
      return;
    }

    // Calculate offset from button to cursor when menu opens (only once)
    // This allows menu to maintain cursor-relative position while moving with button on scroll
    if (buttonRef.current && !cursorOffsetRef.current) {
      const buttonRect = buttonRef.current.getBoundingClientRect();
      cursorOffsetRef.current = {
        x: cursorPosition.x - buttonRect.left,
        y: cursorPosition.y - buttonRect.top,
      };
    }

    const updatePosition = () => {
      if (buttonRef.current && cursorOffsetRef.current) {
        // Use button position + offset to maintain cursor-relative position
        const buttonRect = buttonRef.current.getBoundingClientRect();
        const menuX = buttonRect.left + cursorOffsetRef.current.x;
        const menuY = buttonRect.top + cursorOffsetRef.current.y;
        setPosition({
          top: menuY + MENU_OFFSET_Y,
          right: window.innerWidth - menuX - MENU_OFFSET_X,
        });
      } else if (cursorPosition) {
        // Fallback to cursor position if button ref is not available
        setPosition({
          top: cursorPosition.y + MENU_OFFSET_Y,
          right: window.innerWidth - cursorPosition.x - MENU_OFFSET_X,
        });
      }
    };

    updatePosition();
    window.addEventListener("scroll", updatePosition, true);
    window.addEventListener("resize", updatePosition);

    return () => {
      window.removeEventListener("scroll", updatePosition, true);
      window.removeEventListener("resize", updatePosition);
    };
  }, [isOpen, buttonRef, cursorPosition]);

  return { position };
}
