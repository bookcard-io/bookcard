"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { cn } from "@/libs/utils";

/** Vertical offset for menu positioning (positive = down). */
const MENU_OFFSET_Y = 2;

/** Horizontal offset for menu positioning (negative = left, positive = right). */
const MENU_OFFSET_X = -2;

export interface ProfileMenuProps {
  /** Whether the menu is open. */
  isOpen: boolean;
  /** Callback when menu should be closed. */
  onClose: () => void;
  /** Reference to the button element (for click outside detection). */
  buttonRef: React.RefObject<HTMLElement | null>;
  /** Cursor position when menu was opened. */
  cursorPosition: { x: number; y: number } | null;
  /** Callback when View profile is clicked. */
  onViewProfile?: () => void;
  /** Callback when Logout is clicked. */
  onLogout?: () => void;
}

/**
 * Profile dropdown menu component.
 *
 * Displays a dropdown menu with profile actions.
 * Follows SRP by handling only menu display and item selection.
 * Uses IOC via callback props for actions.
 */
export function ProfileMenu({
  isOpen,
  onClose,
  buttonRef,
  cursorPosition,
  onViewProfile,
  onLogout,
}: ProfileMenuProps) {
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

  const handleItemClick = useCallback(
    (e: React.MouseEvent, handler?: () => void) => {
      e.stopPropagation();
      if (handler) {
        handler();
      }
      onClose();
    },
    [onClose],
  );

  if (!isOpen || !mounted) {
    return null;
  }

  const menuContent = (
    <div
      ref={menuRef}
      className={cn(
        "fixed z-[9999] min-w-[180px] rounded-lg",
        "border border-surface-tonal-a20 bg-surface-tonal-a10",
        "shadow-black/50 shadow-lg",
        "overflow-hidden",
      )}
      style={{
        top: `${position.top}px`,
        right: `${position.right}px`,
      }}
      role="menu"
      aria-label="Profile actions"
      onMouseDown={(e) => e.stopPropagation()}
    >
      <div className="py-1">
        <button
          type="button"
          className={cn(
            "flex w-full items-center gap-3 px-4 py-2.5 text-left",
            "text-sm text-text-a0",
            "hover:bg-surface-tonal-a20",
            "transition-colors duration-150",
            "focus:bg-surface-tonal-a20 focus:outline-none",
          )}
          onClick={(e) => handleItemClick(e, onViewProfile)}
          role="menuitem"
        >
          <i
            className="pi pi-id-card flex-shrink-0 text-base"
            aria-hidden="true"
          />
          <span>View profile</span>
        </button>

        <button
          type="button"
          className={cn(
            "flex w-full items-center gap-3 px-4 py-2.5 text-left",
            "text-sm text-text-a0",
            "hover:bg-surface-tonal-a20",
            "transition-colors duration-150",
            "focus:bg-surface-tonal-a20 focus:outline-none",
          )}
          onClick={(e) => handleItemClick(e, onLogout)}
          role="menuitem"
        >
          <i
            className="pi pi-sign-out flex-shrink-0 text-base"
            aria-hidden="true"
          />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );

  return createPortal(menuContent, document.body);
}
