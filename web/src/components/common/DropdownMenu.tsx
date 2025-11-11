"use client";

import { type ReactNode, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { cn } from "@/libs/utils";

/** Vertical offset for menu positioning (positive = down). */
const MENU_OFFSET_Y = 2;

/** Horizontal offset for menu positioning (negative = left, positive = right). */
const MENU_OFFSET_X = -2;

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
}

/**
 * Base dropdown menu component.
 *
 * Handles positioning, click outside detection, and portal rendering.
 * Follows DRY by centralizing common dropdown menu functionality.
 * Follows SRP by handling only menu display mechanics.
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
}: DropdownMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ top: 0, right: 0 });
  const [mounted, setMounted] = useState(false);

  // Custom click outside handler that excludes the button
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;

      // Don't close if clicking on the menu itself
      if (menuRef.current?.contains(target)) {
        return;
      }

      // Don't close if clicking on the button
      if (buttonRef.current?.contains(target)) {
        return;
      }

      // Close if clicking outside both menu and button
      onClose();
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, buttonRef, onClose]);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!isOpen || !cursorPosition) {
      return;
    }

    const updatePosition = () => {
      if (cursorPosition) {
        // Position menu so top-right corner is at cursor position with offset
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
  }, [isOpen, cursorPosition]);

  if (!isOpen || !mounted) {
    return null;
  }

  const menuContent = (
    <div
      ref={menuRef}
      className={cn(
        "fixed z-[9999] rounded-lg",
        "border border-surface-tonal-a20 bg-surface-tonal-a10",
        "shadow-black/50 shadow-lg",
        "overflow-hidden",
      )}
      style={{
        top: `${position.top}px`,
        right: `${position.right}px`,
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
