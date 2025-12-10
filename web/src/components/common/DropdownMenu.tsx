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

"use client";

import { type ReactNode, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useDropdownClickOutside } from "@/hooks/useDropdownClickOutside";
import { useDropdownPosition } from "@/hooks/useDropdownPosition";
import { cn } from "@/libs/utils";

export interface DropdownMenuProps {
  /** Whether the menu is open. */
  isOpen: boolean;
  /** Callback when menu should be closed. */
  onClose: () => void;
  /** Reference to the button element (for click outside detection). */
  buttonRef: React.RefObject<HTMLElement | null>;
  /** Cursor position when menu was opened. */
  cursorPosition: { x: number; y: number } | null;
  /** Menu content to display. */
  children: ReactNode;
  /** ARIA label for the menu. */
  ariaLabel: string;
  /** Optional minimum width for the menu. */
  minWidth?: number;
  /** Whether to align left edge instead of cursor position. */
  alignLeftEdge?: boolean;
  /** Preferred horizontal alignment. 'left' means left edge aligned (fly right), 'right' means right edge aligned (fly left). Default 'right'. */
  horizontalAlign?: "left" | "right";
  /** Whether to flip horizontal alignment if menu would overflow. */
  autoFlipHorizontal?: boolean;
}

/**
 * Base dropdown menu component.
 *
 * Handles portal rendering and menu display.
 * Follows DRY by centralizing common dropdown menu functionality.
 * Follows SRP by handling only menu presentation.
 * Uses IOC via hooks for positioning and click outside detection.
 *
 * Parameters
 * ----------
 * props : DropdownMenuProps
 *     Component props including open state, callbacks, and children.
 */
export function DropdownMenu({
  isOpen,
  onClose,
  buttonRef,
  cursorPosition,
  children,
  ariaLabel,
  minWidth = 180,
  alignLeftEdge = false,
  horizontalAlign = "right",
  autoFlipHorizontal = false,
}: DropdownMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);

  const { position } = useDropdownPosition({
    isOpen,
    buttonRef,
    cursorPosition,
    menuRef,
    alignLeftEdge,
    horizontalAlign,
    autoFlipHorizontal,
  });

  useDropdownClickOutside({
    isOpen,
    buttonRef,
    menuRef,
    onClose,
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!isOpen || !mounted) {
    return null;
  }

  const menuContent = (
    <div
      ref={menuRef}
      className={cn(
        "fixed z-[9999] rounded-md",
        "border border-surface-tonal-a20 bg-surface-tonal-a10",
        "shadow-black/50 shadow-lg",
        "overflow-hidden",
      )}
      style={{
        top: `${position.top}px`,
        ...(position.left !== undefined
          ? { left: `${position.left}px` }
          : { right: `${position.right}px` }),
        minWidth: `${minWidth}px`,
      }}
      role="menu"
      aria-label={ariaLabel}
      onMouseDown={(e) => e.stopPropagation()}
    >
      <div className="py-1">{children}</div>
    </div>
  );

  return createPortal(menuContent, document.body);
}
