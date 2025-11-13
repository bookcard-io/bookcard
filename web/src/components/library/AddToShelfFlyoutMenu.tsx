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

import { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import { useShelvesContext } from "@/contexts/ShelvesContext";
import { useFlyoutIntent } from "@/hooks/useFlyoutIntent";
import { useFlyoutPosition } from "@/hooks/useFlyoutPosition";
import { useRecentCreatedShelves } from "@/hooks/useRecentCreatedShelves";
import { useRecentShelves } from "@/hooks/useRecentShelves";
import { useShelfActions } from "@/hooks/useShelfActions";
import { cn } from "@/libs/utils";
import { getFlyoutPositionStyle } from "@/utils/flyoutPositionStyle";
import { RecentShelvesSection } from "./RecentShelvesSection";

export interface AddToShelfFlyoutMenuProps {
  /** Whether the flyout menu is open. */
  isOpen: boolean;
  /** Reference to the parent menu item element. */
  parentItemRef: React.RefObject<HTMLElement | null>;
  /** Book ID to add to shelf. */
  bookId: number;
  /** Callback when "Add to shelf..." is clicked to open the modal. */
  onOpenModal: () => void;
  /** Callback when menu should be closed. */
  onClose: () => void;
  /** Callback when mouse enters the flyout (to keep parent menu item hovered). */
  onMouseEnter?: () => void;
  /** Callback when book is successfully added to shelf (to close parent menu). */
  onSuccess?: () => void;
}

/**
 * Flyout menu for adding books to shelves.
 *
 * Displays a submenu with "Add to shelf" option and recent shelves.
 * Positions itself dynamically (left or right) based on available space.
 * Follows SRP by handling only flyout menu display and interactions.
 * Uses IOC via hooks and callback props.
 *
 * Parameters
 * ----------
 * props : AddToShelfFlyoutMenuProps
 *     Component props including open state, parent ref, book ID, and callbacks.
 */
export function AddToShelfFlyoutMenu({
  isOpen,
  parentItemRef,
  bookId,
  onOpenModal,
  onClose,
  onMouseEnter,
  onSuccess,
}: AddToShelfFlyoutMenuProps) {
  const [mounted, setMounted] = useState(false);

  const { shelves, refresh: refreshShelvesContext } = useShelvesContext();
  const { addBook, isProcessing } = useShelfActions();
  const { addRecentShelf } = useRecentShelves();
  const recentShelves = useRecentCreatedShelves(shelves);

  const { position, direction, menuRef } = useFlyoutPosition({
    isOpen,
    parentItemRef,
    mounted,
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  // Keep flyout open while pointer is within padded union of parent + flyout
  useFlyoutIntent({
    isOpen,
    parentItemRef,
    menuRef,
    onClose,
    padding: 10,
  });

  /**
   * Handle mouse entering the flyout menu.
   */
  const handleFlyoutMouseEnter = useCallback(() => {
    onMouseEnter?.();
  }, [onMouseEnter]);

  /**
   * Handle "Add to shelf..." menu item click - open the modal.
   */
  const handleAddToShelfClick = useCallback(() => {
    onOpenModal();
  }, [onOpenModal]);

  /**
   * Handle adding book to a shelf (from recent shelves in flyout).
   *
   * Parameters
   * ----------
   * shelfId : number
   *     Shelf ID to add book to.
   */
  const handleAddToShelf = useCallback(
    async (shelfId: number) => {
      try {
        await addBook(shelfId, bookId);
        addRecentShelf(shelfId);
        // Refresh shelves context to update book counts
        await refreshShelvesContext();
        onClose();
        // Close parent menu on success
        onSuccess?.();
      } catch (error) {
        // If book is already in shelf, treat as success (no-op) and close menu
        const errorMessage =
          error instanceof Error ? error.message : String(error);
        if (
          errorMessage.toLowerCase().includes("already in shelf") ||
          errorMessage.toLowerCase().includes("already exists")
        ) {
          // Silently no-op and close menus
          onClose();
          onSuccess?.();
          return;
        }
        // For other errors, log and don't close menu
        console.error("Failed to add book to shelf:", error);
      }
    },
    [
      addBook,
      bookId,
      addRecentShelf,
      refreshShelvesContext,
      onClose,
      onSuccess,
    ],
  );

  if (!isOpen || !mounted) {
    return null;
  }

  const menuContent = (
    <div
      ref={menuRef}
      className={cn(
        "fixed z-[10000] rounded-lg",
        "border border-surface-tonal-a20 bg-surface-tonal-a10",
        "shadow-black/50 shadow-lg",
        "overflow-hidden",
        "min-w-[200px]",
      )}
      style={getFlyoutPositionStyle(position, direction)}
      role="menu"
      aria-label="Add to shelf"
      onMouseDown={(e) => e.stopPropagation()}
      onMouseEnter={handleFlyoutMouseEnter}
    >
      <div className="py-1">
        <DropdownMenuItem
          label="Add to shelf..."
          onClick={handleAddToShelfClick}
          disabled={isProcessing}
        />
        <RecentShelvesSection
          shelves={recentShelves}
          onShelfClick={handleAddToShelf}
          disabled={isProcessing}
        />
      </div>
    </div>
  );

  return createPortal(menuContent, document.body);
}
