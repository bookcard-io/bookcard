"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { LibraryBuilding } from "@/icons/LibraryBuilding";
import { InterfaceContentBook2LibraryContentBooksBookShelfStack as Shelf } from "@/icons/Shelf";
import { cn } from "@/libs/utils";

/** Vertical offset for menu positioning (positive = down). */
const MENU_OFFSET_Y = 2;

/** Horizontal offset for menu positioning (negative = left, positive = right). */
const MENU_OFFSET_X = -2;

export interface BookCardMenuProps {
  /** Whether the menu is open. */
  isOpen: boolean;
  /** Callback when menu should be closed. */
  onClose: () => void;
  /** Reference to the button element (for click outside detection). */
  buttonRef: React.RefObject<HTMLElement | null>;
  /** Cursor position when menu was opened. */
  cursorPosition: { x: number; y: number } | null;
  /** Callback when Book info is clicked. */
  onBookInfo?: () => void;
  /** Callback when Send is clicked. */
  onSend?: () => void;
  /** Callback when Move to library is clicked. */
  onMoveToLibrary?: () => void;
  /** Callback when Move to shelf is clicked. */
  onMoveToShelf?: () => void;
  /** Callback when Convert is clicked. */
  onConvert?: () => void;
  /** Callback when Delete is clicked. */
  onDelete?: () => void;
  /** Callback when More is clicked. */
  onMore?: () => void;
}

/**
 * Book card context menu component.
 *
 * Displays a dropdown menu with book actions.
 * Follows SRP by handling only menu display and item selection.
 * Uses IOC via callback props for actions.
 */
export function BookCardMenu({
  isOpen,
  onClose,
  buttonRef,
  cursorPosition,
  onBookInfo,
  onSend,
  onMoveToLibrary,
  onMoveToShelf,
  onConvert,
  onDelete,
  onMore,
}: BookCardMenuProps) {
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
      aria-label="Book actions"
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
          onClick={(e) => handleItemClick(e, onBookInfo)}
          role="menuitem"
        >
          <i
            className="pi pi-info-circle flex-shrink-0 text-base"
            aria-hidden="true"
          />
          <span>Book info</span>
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
          onClick={(e) => handleItemClick(e, onSend)}
          role="menuitem"
        >
          <i
            className="pi pi-send flex-shrink-0 text-base"
            aria-hidden="true"
          />
          <span>Send</span>
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
          onClick={(e) => handleItemClick(e, onMoveToLibrary)}
          role="menuitem"
        >
          <LibraryBuilding className="h-4 w-4 flex-shrink-0" />
          <span>Move to library</span>
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
          onClick={(e) => handleItemClick(e, onMoveToShelf)}
          role="menuitem"
        >
          <Shelf className="h-4 w-4 flex-shrink-0" />
          <span>Add to shelf</span>
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
          onClick={(e) => handleItemClick(e, onConvert)}
          role="menuitem"
        >
          <i
            className="pi pi-arrow-right-arrow-left flex-shrink-0 text-base"
            aria-hidden="true"
          />
          <span>Convert format</span>
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
          onClick={(e) => handleItemClick(e, onDelete)}
          role="menuitem"
        >
          <i
            className="pi pi-trash flex-shrink-0 text-base"
            aria-hidden="true"
          />
          <span>Delete</span>
        </button>

        <hr className="my-1 h-px border-0 bg-surface-tonal-a20" />

        <button
          type="button"
          className={cn(
            "flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left",
            "text-sm text-text-a0",
            "hover:bg-surface-tonal-a20",
            "transition-colors duration-150",
            "focus:bg-surface-tonal-a20 focus:outline-none",
          )}
          onClick={(e) => handleItemClick(e, onMore)}
          role="menuitem"
        >
          <span>More...</span>
          <i
            className="pi pi-chevron-right flex-shrink-0 text-xs"
            aria-hidden="true"
          />
        </button>
      </div>
    </div>
  );

  return createPortal(menuContent, document.body);
}
