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

import { useLayoutEffect, useRef, useState } from "react";

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
  /** Optional ref to the menu element to allow measuring height for auto-flip. */
  menuRef?: React.RefObject<HTMLElement | null>;
  /** Whether to align left edge instead of cursor position. */
  alignLeftEdge?: boolean;
  /** Preferred horizontal alignment. 'left' aligns left edge (fly right), 'right' aligns right edge (fly left). */
  horizontalAlign?: "left" | "right";
  /** Whether to flip horizontal alignment if menu would overflow. */
  autoFlipHorizontal?: boolean;
}

export interface UseDropdownPositionResult {
  /** Calculated position for the menu (top and right/left in pixels). */
  position: { top: number; right?: number; left?: number };
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
  menuRef,
  alignLeftEdge = false,
  horizontalAlign = "right",
  autoFlipHorizontal = false,
}: UseDropdownPositionOptions): UseDropdownPositionResult {
  const [position, setPosition] = useState<{
    top: number;
    right?: number;
    left?: number;
  }>({ top: 0, right: 0 });
  const cursorOffsetRef = useRef<{ x: number; y: number } | null>(null);

  // Use layout effect so the first measurement/position happens before paint,
  // preventing a visible jump from down->up when the menu would overflow.
  useLayoutEffect(() => {
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

        const menuRect = menuRef?.current?.getBoundingClientRect();
        const measuredHeight = menuRect?.height || 0;
        const measuredWidth = menuRect?.width || 0;

        // Auto-flip up if menu would overflow the bottom edge
        const downTop = menuY + MENU_OFFSET_Y;
        const wouldOverflowY = downTop + measuredHeight > window.innerHeight;
        let top = wouldOverflowY
          ? Math.max(0, menuY - measuredHeight - MENU_OFFSET_Y)
          : downTop;

        // Determine horizontal alignment
        // alignLeftEdge forces 'left' and implies specific offset logic (legacy)
        let finalAlign = alignLeftEdge ? "left" : horizontalAlign;

        if (autoFlipHorizontal && measuredWidth > 0) {
          if (finalAlign === "left") {
            // Check if it overflows right edge
            if (menuX + measuredWidth > window.innerWidth) {
              finalAlign = "right";
            }
          } else {
            // Check if it overflows left edge (when right-aligned, it extends left from menuX)
            if (menuX - measuredWidth < 0) {
              finalAlign = "left";
            }
          }
        }

        if (alignLeftEdge && finalAlign === "left") {
          // Add 1rem (16px) vertical offset for left-edge aligned menus
          // Legacy behavior for LibraryFilterBar
          top += 8;
        }

        if (finalAlign === "left") {
          setPosition({
            top,
            left: menuX,
          });
        } else {
          setPosition({
            top,
            right: window.innerWidth - menuX - MENU_OFFSET_X,
          });
        }
      } else {
        // Fallback to cursor position if button ref is not available
        const menuRect = menuRef?.current?.getBoundingClientRect();
        const measuredHeight = menuRect?.height || 0;
        const measuredWidth = menuRect?.width || 0;

        const downTop = cursorPosition.y + MENU_OFFSET_Y;
        const wouldOverflowY = downTop + measuredHeight > window.innerHeight;
        let top = wouldOverflowY
          ? Math.max(0, cursorPosition.y - measuredHeight - MENU_OFFSET_Y)
          : downTop;

        let finalAlign = alignLeftEdge ? "left" : horizontalAlign;

        if (autoFlipHorizontal && measuredWidth > 0) {
          if (finalAlign === "left") {
            if (cursorPosition.x + measuredWidth > window.innerWidth) {
              finalAlign = "right";
            }
          } else {
            if (cursorPosition.x - measuredWidth < 0) {
              finalAlign = "left";
            }
          }
        }

        if (alignLeftEdge && finalAlign === "left") {
          top += 8;
        }

        if (finalAlign === "left") {
          setPosition({
            top,
            left: cursorPosition.x,
          });
        } else {
          setPosition({
            top,
            right: window.innerWidth - cursorPosition.x - MENU_OFFSET_X,
          });
        }
      }
    };

    updatePosition();
    window.addEventListener("scroll", updatePosition, true);
    window.addEventListener("resize", updatePosition);

    return () => {
      window.removeEventListener("scroll", updatePosition, true);
      window.removeEventListener("resize", updatePosition);
    };
  }, [
    isOpen,
    buttonRef,
    cursorPosition,
    menuRef,
    alignLeftEdge,
    horizontalAlign,
    autoFlipHorizontal,
  ]);

  return { position };
}
