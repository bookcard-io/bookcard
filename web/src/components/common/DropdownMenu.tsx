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
}: DropdownMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);

  const { position } = useDropdownPosition({
    isOpen,
    buttonRef,
    cursorPosition,
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
