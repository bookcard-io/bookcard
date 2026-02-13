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

import { useCallback, useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import { useShelvesContext } from "@/contexts/ShelvesContext";
import { useUser } from "@/contexts/UserContext";
import { useFlyoutIntent } from "@/hooks/useFlyoutIntent";
import { useFlyoutPosition } from "@/hooks/useFlyoutPosition";
import { useRecentCreatedShelves } from "@/hooks/useRecentCreatedShelves";
import { useRecentShelves } from "@/hooks/useRecentShelves";
import { useShelfActions } from "@/hooks/useShelfActions";
import { cn } from "@/libs/utils";
import type { Book } from "@/types/book";
import { getFlyoutPositionStyle } from "@/utils/flyoutPositionStyle";
import { isMagicShelf } from "@/utils/shelfUtils";
import { RecentShelvesSection } from "./RecentShelvesSection";

export interface AddToShelfFlyoutMenuProps {
  /** Whether the flyout menu is open. */
  isOpen: boolean;
  /** Reference to the parent menu item element. */
  parentItemRef: React.RefObject<HTMLElement | null>;
  /** Books to add to shelf. If not provided, uses selected books from context. */
  books?: Book[];
  /** Callback when "Add to shelf..." is clicked to open the modal. */
  onOpenModal: () => void;
  /** Callback when menu should be closed. */
  onClose: () => void;
  /** Callback when mouse enters the flyout (to keep parent menu item hovered). */
  onMouseEnter?: () => void;
  /** Callback when books are successfully added to shelf (to close parent menu). */
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
  books: booksProp,
  onOpenModal,
  onClose,
  onMouseEnter,
  onSuccess,
}: AddToShelfFlyoutMenuProps) {
  const { canPerformAction } = useUser();
  const { showDanger } = useGlobalMessages();
  const canEditShelves = canPerformAction("shelves", "edit");
  const [mounted, setMounted] = useState(false);

  // Get books from context if not provided via prop
  const { selectedBookIds, books: contextBooks } = useSelectedBooks();
  const books = useMemo(() => {
    if (booksProp) {
      return booksProp;
    }
    // Use selected books from context
    if (selectedBookIds.size === 0 || contextBooks.length === 0) {
      return [];
    }
    return contextBooks.filter((book) => selectedBookIds.has(book.id));
  }, [booksProp, selectedBookIds, contextBooks]);

  const { shelves, refresh: refreshShelvesContext } = useShelvesContext();
  const { addBook, isProcessing } = useShelfActions();
  const { addRecentShelf } = useRecentShelves();
  const recentShelvesAll = useRecentCreatedShelves(shelves);
  const recentShelves = useMemo(() => {
    return recentShelvesAll.filter((shelf) => !isMagicShelf(shelf));
  }, [recentShelvesAll]);

  const { position, direction, menuRef } = useFlyoutPosition({
    isOpen,
    parentItemRef,
    mounted,
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  // Keep flyout open while pointer is within padded union of parent + flyout,
  // but close quickly once the pointer "rests" elsewhere to keep the UI snappy.
  useFlyoutIntent({
    isOpen,
    parentItemRef,
    menuRef,
    onClose,
    padding: 10,
    minMovementPx: 2,
    idleTimeMs: 20, // smaller value = snappier close; larger value = more forgiving, but sluggish
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
   * Handle adding books to a shelf (from recent shelves in flyout).
   *
   * Adds all books to the shelf. If any book is already in the shelf,
   * it's skipped (no-op). Only shows error if all books fail.
   *
   * Parameters
   * ----------
   * shelfId : number
   *     Shelf ID to add books to.
   */
  const handleAddToShelf = useCallback(
    async (shelfId: number) => {
      if (books.length === 0) {
        return;
      }

      const results = await Promise.allSettled(
        books
          .filter(
            (b): b is typeof b & { library_id: number } => b.library_id != null,
          )
          .map((book) => addBook(shelfId, book.id, book.library_id)),
      );

      const successful = results.filter((r) => r.status === "fulfilled").length;
      const failed = results.filter((r) => r.status === "rejected").length;

      // If at least one book was added successfully, mark shelf as recent
      if (successful > 0) {
        addRecentShelf(shelfId);
      }

      // Check if all failures are due to books already being in shelf
      const allAlreadyInShelf = results
        .filter((r) => r.status === "rejected")
        .every((r) => {
          const errorMessage =
            r.reason instanceof Error ? r.reason.message : String(r.reason);
          return (
            errorMessage.toLowerCase().includes("already in shelf") ||
            errorMessage.toLowerCase().includes("already exists")
          );
        });

      // If all books are already in shelf or all succeeded, treat as success
      if (failed === 0 || allAlreadyInShelf) {
        // Refresh shelves context to update book counts
        await refreshShelvesContext();
        onClose();
        // Close parent menu on success
        onSuccess?.();
        return;
      }

      // If some books failed for other reasons, show error but still close menu
      // (some books may have been added successfully)
      if (failed > 0) {
        const errorMessages = results
          .filter((r) => r.status === "rejected")
          .map((r) => {
            const errorMessage =
              r.reason instanceof Error
                ? r.reason.message
                : "Failed to add book";
            return errorMessage;
          });
        const uniqueErrors = [...new Set(errorMessages)];
        showDanger(uniqueErrors[0] || "Failed to add some books to shelf");
      }

      // Refresh shelves context and close menu
      await refreshShelvesContext();
      onClose();
      onSuccess?.();
    },
    [
      books,
      addBook,
      addRecentShelf,
      refreshShelvesContext,
      onClose,
      onSuccess,
      showDanger,
    ],
  );

  if (!isOpen || !mounted) {
    return null;
  }

  const menuContent = (
    <div
      ref={menuRef}
      className={cn(
        "fixed z-[10000] rounded-md",
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
      data-keep-selection
    >
      <div className="py-1">
        <DropdownMenuItem
          label="Add to shelf..."
          onClick={canEditShelves ? handleAddToShelfClick : undefined}
          disabled={!canEditShelves || isProcessing}
        />
        <RecentShelvesSection
          shelves={recentShelves}
          onShelfClick={handleAddToShelf}
          disabled={!canEditShelves || isProcessing}
        />
      </div>
    </div>
  );

  return createPortal(menuContent, document.body);
}
