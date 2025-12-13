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

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import { useExclusiveFlyoutMenus } from "@/hooks/useExclusiveFlyoutMenus";
import { useFlyoutMenu } from "@/hooks/useFlyoutMenu";
import { LibraryBuilding } from "@/icons/LibraryBuilding";
import { OutlineMerge } from "@/icons/OutlineMerge";
import { cn } from "@/libs/utils";
import { AddToShelfFlyoutMenu } from "../AddToShelfFlyoutMenu";
import { AddToShelfMenuItem } from "../AddToShelfMenuItem";
import { AddToShelfModal } from "../AddToShelfModal";
import { SendToDeviceFlyoutMenu } from "../SendToDeviceFlyoutMenu";
import { SendToDeviceMenuItem } from "../SendToDeviceMenuItem";

export interface WithSelectedDropdownProps {
  /**
   * Callback fired when the dropdown is clicked.
   */
  onClick?: () => void;
  /**
   * Whether Send action is disabled.
   */
  isSendDisabled?: boolean;
  /**
   * Whether the dropdown is disabled.
   */
  disabled?: boolean;
}

/**
 * Dropdown button component for bulk actions on selected items.
 *
 * Provides a dropdown interface for performing actions on multiple selected items.
 * Follows SRP by handling only dropdown display and item selection.
 * Uses IOC via callback props for actions.
 * Follows DRY by using shared DropdownMenuItem components.
 */
export function WithSelectedDropdown({
  onClick,
  isSendDisabled = false,
  disabled = false,
}: WithSelectedDropdownProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showAddToShelfModal, setShowAddToShelfModal] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const { selectedBookIds, books } = useSelectedBooks();

  // Get all selected books
  const selectedBooks = useMemo(() => {
    if (selectedBookIds.size === 0 || books.length === 0) {
      return [];
    }
    return books.filter((book) => selectedBookIds.has(book.id));
  }, [selectedBookIds, books]);

  const addToShelfFlyoutMenu = useFlyoutMenu({ parentMenuOpen: isMenuOpen });
  const sendFlyoutMenu = useFlyoutMenu({ parentMenuOpen: isMenuOpen });

  // Ensure only one flyout menu is open at a time
  const { handleFirstMouseEnter, handleSecondMouseEnter } =
    useExclusiveFlyoutMenus(addToShelfFlyoutMenu, sendFlyoutMenu);

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (disabled) {
      return;
    }
    setIsMenuOpen((prev) => !prev);
    onClick?.();
  };

  const handleMenuClose = () => {
    setIsMenuOpen(false);
  };

  // Handle click outside to close panel
  // Exclude clicks on the button
  useEffect(() => {
    if (!isMenuOpen) {
      return;
    }

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;

      // Don't close if clicking on the button or its children
      const isWithSelectedButton = target.closest(
        "[data-with-selected-button]",
      );
      if (isWithSelectedButton) {
        return;
      }

      // Don't close if clicking inside the panel
      if (panelRef.current?.contains(target)) {
        return;
      }

      // Close if clicking outside
      setIsMenuOpen(false);
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isMenuOpen]);

  /**
   * Handle "Add to..." menu item click.
   *
   * Note: The flyout menu opens on hover, so clicking the parent item
   * doesn't need to do anything. The actual functionality is in the flyout.
   */
  const handleAddToClick = useCallback(() => {
    // No-op: flyout opens on hover, functionality is in flyout menu
  }, []);

  /**
   * Handle "Send to..." menu item click.
   *
   * Note: The flyout menu opens on hover, so clicking the parent item
   * doesn't need to do anything. The actual functionality is in the flyout.
   */
  const handleSendToClick = useCallback(() => {
    // No-op: flyout opens on hover, functionality is in flyout menu
  }, []);

  // No-op handlers for all actions
  const handleBatchEdit = () => {
    handleMenuClose();
    // No-op
  };

  const handleMoveToLibrary = () => {
    handleMenuClose();
    // No-op
  };

  const handleConvert = () => {
    handleMenuClose();
    // No-op
  };

  const handleDelete = () => {
    handleMenuClose();
    // No-op
  };

  const handleMerge = () => {
    handleMenuClose();
    // No-op
  };

  return (
    <div className="relative">
      <button
        type="button"
        className={cn(
          "btn-tonal group flex cursor-pointer items-center gap-2 whitespace-nowrap px-4 py-2.5 font-inherit",
        )}
        onClick={handleClick}
        aria-label="Actions with selected items"
        aria-haspopup="true"
        aria-expanded={isMenuOpen}
        data-with-selected-button
      >
        <span className="leading-none">With selected</span>
        <i
          className={cn(
            "pi pi-chevron-down h-4 w-4 flex-shrink-0 text-text-a30 transition-[color,transform] duration-200 group-hover:text-text-a0",
            isMenuOpen && "rotate-180",
          )}
          aria-hidden="true"
        />
      </button>
      {isMenuOpen && (
        <div
          className="absolute top-[calc(100%+8px)] left-0 z-[100] flex min-w-[180px] flex-col overflow-hidden rounded-md border border-surface-tonal-a20 bg-surface-tonal-a10 shadow-black/50 shadow-lg"
          ref={panelRef}
          role="menu"
          aria-label="Actions with selected items"
          data-with-selected-panel
          onMouseDown={(e) => e.stopPropagation()}
        >
          <div className="transition-colors duration-150 hover:bg-surface-tonal-a20">
            <DropdownMenuItem
              icon="pi pi-pencil"
              label="Batch edit"
              onClick={handleBatchEdit}
              className="hover:bg-transparent"
            />
          </div>
          <div className="transition-colors duration-150 hover:bg-surface-tonal-a20">
            <SendToDeviceMenuItem
              itemRef={sendFlyoutMenu.parentItemRef}
              onMouseEnter={handleSecondMouseEnter}
              onMouseLeave={sendFlyoutMenu.handleParentMouseLeave}
              onClick={handleSendToClick}
              books={selectedBooks}
              disabled={isSendDisabled}
            />
          </div>
          <div className="transition-colors duration-150 hover:bg-surface-tonal-a20">
            <DropdownMenuItem
              icon={<LibraryBuilding className="h-4 w-4" />}
              label="Move to library"
              onClick={handleMoveToLibrary}
              className="hover:bg-transparent"
            />
          </div>
          <div className="transition-colors duration-150 hover:bg-surface-tonal-a20">
            <AddToShelfMenuItem
              itemRef={addToShelfFlyoutMenu.parentItemRef}
              onMouseEnter={handleFirstMouseEnter}
              onMouseLeave={addToShelfFlyoutMenu.handleParentMouseLeave}
              onClick={handleAddToClick}
            />
          </div>
          <div className="transition-colors duration-150 hover:bg-surface-tonal-a20">
            <DropdownMenuItem
              icon="pi pi-arrow-right-arrow-left"
              label="Convert"
              onClick={handleConvert}
              className="hover:bg-transparent"
            />
          </div>
          <div className="transition-colors duration-150 hover:bg-surface-tonal-a20">
            <DropdownMenuItem
              icon="pi pi-trash"
              label="Delete"
              onClick={handleDelete}
              className="hover:bg-transparent"
            />
          </div>
          <div className="transition-colors duration-150 hover:bg-surface-tonal-a20">
            <DropdownMenuItem
              icon={<OutlineMerge className="h-4 w-4" />}
              label="Merge"
              onClick={handleMerge}
              className="hover:bg-transparent"
            />
          </div>
        </div>
      )}
      {isMenuOpen && selectedBooks.length > 0 && (
        <>
          <AddToShelfFlyoutMenu
            isOpen={addToShelfFlyoutMenu.isFlyoutOpen && isMenuOpen}
            parentItemRef={addToShelfFlyoutMenu.parentItemRef}
            onOpenModal={() => {
              addToShelfFlyoutMenu.handleFlyoutClose();
              handleMenuClose();
              setShowAddToShelfModal(true);
            }}
            onClose={addToShelfFlyoutMenu.handleFlyoutClose}
            onMouseEnter={addToShelfFlyoutMenu.handleFlyoutMouseEnter}
            onSuccess={handleMenuClose}
          />
          <SendToDeviceFlyoutMenu
            isOpen={sendFlyoutMenu.isFlyoutOpen && isMenuOpen}
            parentItemRef={sendFlyoutMenu.parentItemRef}
            onClose={sendFlyoutMenu.handleFlyoutClose}
            onMouseEnter={sendFlyoutMenu.handleFlyoutMouseEnter}
            onSuccess={handleMenuClose}
            onCloseParent={handleMenuClose}
          />
        </>
      )}
      {showAddToShelfModal && (
        <AddToShelfModal
          onClose={() => {
            setShowAddToShelfModal(false);
            handleMenuClose();
          }}
          onSuccess={handleMenuClose}
        />
      )}
    </div>
  );
}
