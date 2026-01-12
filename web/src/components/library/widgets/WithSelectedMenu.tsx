// Copyright (C) 2026 knguyen and others
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

import { useCallback } from "react";
import { DropdownMenu } from "@/components/common/DropdownMenu";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import { AddToShelfFlyoutMenu } from "@/components/library/AddToShelfFlyoutMenu";
import { AddToShelfMenuItem } from "@/components/library/AddToShelfMenuItem";
import { SendToDeviceFlyoutMenu } from "@/components/library/SendToDeviceFlyoutMenu";
import { SendToDeviceMenuItem } from "@/components/library/SendToDeviceMenuItem";
import { useExclusiveFlyoutMenus } from "@/hooks/useExclusiveFlyoutMenus";
import { useFlyoutMenu } from "@/hooks/useFlyoutMenu";
import type { UseWithSelectedMenuActionsResult } from "@/hooks/useWithSelectedMenuActions";
import { LibraryBuilding } from "@/icons/LibraryBuilding";
import { OutlineMerge } from "@/icons/OutlineMerge";
import type { Book } from "@/types/book";

export interface WithSelectedMenuProps {
  /** Whether the menu is open. */
  isOpen: boolean;
  /** Callback when menu should be closed. */
  onClose: () => void;
  /** Reference to the button element (for click outside detection). */
  buttonRef: React.RefObject<HTMLElement | null>;
  /** Cursor position when menu was opened. */
  cursorPosition: { x: number; y: number } | null;
  /** Selected books. */
  selectedBooks: Book[];
  /** Actions and state for the menu items. */
  actions: UseWithSelectedMenuActionsResult;
}

/**
 * Menu for "With selected" dropdown.
 *
 * Displays a dropdown menu with actions for selected books.
 * Follows SRP by handling only menu display and item selection.
 * Uses IOC via callback props for actions.
 */
export function WithSelectedMenu({
  isOpen,
  onClose,
  buttonRef,
  cursorPosition,
  selectedBooks,
  actions,
}: WithSelectedMenuProps) {
  const {
    onBatchEdit,
    onMoveToLibrary,
    onConvert,
    onDelete,
    onMerge,
    onAddToShelf,
    isSendDisabled,
  } = actions;

  const addToShelfFlyoutMenu = useFlyoutMenu({ parentMenuOpen: isOpen });
  const sendFlyoutMenu = useFlyoutMenu({ parentMenuOpen: isOpen });

  // Ensure only one flyout menu is open at a time
  const { handleFirstMouseEnter, handleSecondMouseEnter } =
    useExclusiveFlyoutMenus(addToShelfFlyoutMenu, sendFlyoutMenu);

  /**
   * Handle menu item click.
   */
  const handleItemClick = useCallback(
    (handler: () => void) => {
      handler();
      onClose();
    },
    [onClose],
  );

  /**
   * Handle "Add to..." menu item click.
   */
  const handleAddToClick = useCallback(() => {
    // No-op: flyout opens on hover
  }, []);

  /**
   * Handle "Send to..." menu item click.
   */
  const handleSendToClick = useCallback(() => {
    // No-op: flyout opens on hover
  }, []);

  return (
    <>
      <DropdownMenu
        isOpen={isOpen}
        onClose={onClose}
        buttonRef={buttonRef}
        cursorPosition={cursorPosition}
        ariaLabel="Actions with selected items"
        alignLeftEdge
        minWidth={180}
      >
        <DropdownMenuItem
          icon="pi pi-pencil"
          label="Batch edit"
          onClick={() => handleItemClick(onBatchEdit)}
        />
        <SendToDeviceMenuItem
          itemRef={sendFlyoutMenu.parentItemRef}
          onMouseEnter={handleSecondMouseEnter}
          onMouseLeave={sendFlyoutMenu.handleParentMouseLeave}
          onClick={handleSendToClick}
          books={selectedBooks}
          disabled={isSendDisabled}
        />
        <DropdownMenuItem
          icon={<LibraryBuilding className="h-4 w-4" />}
          label="Move to library"
          onClick={() => handleItemClick(onMoveToLibrary)}
        />
        <AddToShelfMenuItem
          itemRef={addToShelfFlyoutMenu.parentItemRef}
          onMouseEnter={handleFirstMouseEnter}
          onMouseLeave={addToShelfFlyoutMenu.handleParentMouseLeave}
          onClick={handleAddToClick}
        />
        <DropdownMenuItem
          icon="pi pi-arrow-right-arrow-left"
          label="Convert"
          onClick={() => handleItemClick(onConvert)}
        />
        <DropdownMenuItem
          icon="pi pi-trash"
          label="Delete"
          onClick={() => handleItemClick(onDelete)}
        />
        <DropdownMenuItem
          icon={<OutlineMerge className="h-4 w-4" />}
          label="Merge"
          onClick={() => handleItemClick(onMerge)}
        />
      </DropdownMenu>
      {isOpen && (
        <>
          <AddToShelfFlyoutMenu
            isOpen={addToShelfFlyoutMenu.isFlyoutOpen}
            parentItemRef={addToShelfFlyoutMenu.parentItemRef}
            books={selectedBooks}
            onOpenModal={() => {
              onAddToShelf();
              addToShelfFlyoutMenu.handleFlyoutClose();
              onClose();
            }}
            onClose={addToShelfFlyoutMenu.handleFlyoutClose}
            onMouseEnter={addToShelfFlyoutMenu.handleFlyoutMouseEnter}
            onSuccess={onClose}
          />
          <SendToDeviceFlyoutMenu
            isOpen={sendFlyoutMenu.isFlyoutOpen}
            parentItemRef={sendFlyoutMenu.parentItemRef}
            books={selectedBooks}
            onClose={sendFlyoutMenu.handleFlyoutClose}
            onMouseEnter={sendFlyoutMenu.handleFlyoutMouseEnter}
            onSuccess={onClose}
            onCloseParent={onClose}
          />
        </>
      )}
    </>
  );
}
