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

import { useCallback } from "react";
import { DropdownMenu } from "@/components/common/DropdownMenu";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import { useUser } from "@/contexts/UserContext";
import { useExclusiveFlyoutMenus } from "@/hooks/useExclusiveFlyoutMenus";
import { useFlyoutMenu } from "@/hooks/useFlyoutMenu";
import { LibraryBuilding } from "@/icons/LibraryBuilding";
import { cn } from "@/libs/utils";
import type { Book } from "@/types/book";
import { buildBookPermissionContext } from "@/utils/permissions";
import { AddToShelfFlyoutMenu } from "./AddToShelfFlyoutMenu";
import { AddToShelfMenuItem } from "./AddToShelfMenuItem";
import { SendToDeviceFlyoutMenu } from "./SendToDeviceFlyoutMenu";
import { SendToDeviceMenuItem } from "./SendToDeviceMenuItem";

export interface BookCardMenuProps {
  /** Whether the menu is open. */
  isOpen: boolean;
  /** Callback when menu should be closed. */
  onClose: () => void;
  /** Reference to the button element (for click outside detection). */
  buttonRef: React.RefObject<HTMLElement | null>;
  /** Cursor position when menu was opened. */
  cursorPosition: { x: number; y: number } | null;
  /** Book data (required for operations and permission checking). */
  book: Book;
  /** Callback when Book info is clicked. */
  onBookInfo?: () => void;
  /** Whether Send action is disabled. */
  isSendDisabled?: boolean;
  /** Callback when Move to library is clicked. */
  onMoveToLibrary?: () => void;
  /** Callback when Convert is clicked. */
  onConvert?: () => void;
  /** Callback when Delete is clicked. */
  onDelete?: () => void;
  /** Callback when More is clicked. */
  onMore?: () => void;
  /** Callback when Add to shelf modal should be opened. */
  onOpenAddToShelfModal?: () => void;
}

/**
 * Book card context menu component.
 *
 * Displays a dropdown menu with book actions.
 * Follows SRP by handling only menu display and item selection.
 * Uses IOC via callback props for actions.
 * Follows DRY by using shared DropdownMenu and DropdownMenuItem components.
 */
export function BookCardMenu({
  isOpen,
  onClose,
  buttonRef,
  cursorPosition,
  book,
  onBookInfo,
  onMoveToLibrary,
  onConvert,
  onDelete,
  onMore,
  isSendDisabled = false,
  onOpenAddToShelfModal,
}: BookCardMenuProps) {
  const { user, canPerformAction } = useUser();
  const bookContext = buildBookPermissionContext(book);
  const canWrite = canPerformAction("books", "write", bookContext);
  const canDelete = canPerformAction("books", "delete", bookContext);
  const isAdmin = user?.is_admin ?? false;

  const flyoutMenu = useFlyoutMenu({ parentMenuOpen: isOpen });
  const sendFlyoutMenu = useFlyoutMenu({ parentMenuOpen: isOpen });

  // Ensure only one flyout menu is open at a time
  const { handleFirstMouseEnter, handleSecondMouseEnter } =
    useExclusiveFlyoutMenus(flyoutMenu, sendFlyoutMenu);

  /**
   * Handle menu item click.
   *
   * Parameters
   * ----------
   * handler : (() => void) | undefined
   *     Optional handler to execute before closing menu.
   */
  const handleItemClick = useCallback(
    (handler?: () => void) => {
      if (handler) {
        handler();
      }
      onClose();
    },
    [onClose],
  );

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

  return (
    <>
      <DropdownMenu
        isOpen={isOpen}
        onClose={onClose}
        buttonRef={buttonRef}
        cursorPosition={cursorPosition}
        ariaLabel="Book actions"
        horizontalAlign="right"
        autoFlipHorizontal
      >
        <DropdownMenuItem
          icon="pi pi-info-circle"
          label="Book info"
          onClick={() => handleItemClick(onBookInfo)}
        />
        <SendToDeviceMenuItem
          itemRef={sendFlyoutMenu.parentItemRef}
          onMouseEnter={handleSecondMouseEnter}
          onMouseLeave={sendFlyoutMenu.handleParentMouseLeave}
          onClick={handleSendToClick}
          books={[book]}
          disabled={isSendDisabled}
        />
        <DropdownMenuItem
          icon={<LibraryBuilding className="h-4 w-4" />}
          label="Move to library"
          onClick={isAdmin ? () => handleItemClick(onMoveToLibrary) : undefined}
          disabled={!isAdmin}
        />
        <AddToShelfMenuItem
          itemRef={flyoutMenu.parentItemRef}
          onMouseEnter={handleFirstMouseEnter}
          onMouseLeave={flyoutMenu.handleParentMouseLeave}
          onClick={handleAddToClick}
        />
        <DropdownMenuItem
          icon="pi pi-arrow-right-arrow-left"
          label="Convert format"
          onClick={canWrite ? () => handleItemClick(onConvert) : undefined}
          disabled={!canWrite}
        />
        <DropdownMenuItem
          icon="pi pi-trash"
          label="Delete"
          onClick={canDelete ? () => handleItemClick(onDelete) : undefined}
          disabled={!canDelete}
        />
        <hr className={cn("my-1 h-px border-0 bg-surface-tonal-a20")} />
        <DropdownMenuItem
          label="More..."
          onClick={() => handleItemClick(onMore)}
          rightContent={
            <i
              className="pi pi-chevron-right flex-shrink-0 text-xs"
              aria-hidden="true"
            />
          }
          justifyBetween
        />
      </DropdownMenu>
      {isOpen && (
        <>
          <AddToShelfFlyoutMenu
            isOpen={flyoutMenu.isFlyoutOpen}
            parentItemRef={flyoutMenu.parentItemRef}
            books={[book]}
            onOpenModal={() => {
              onOpenAddToShelfModal?.();
              flyoutMenu.handleFlyoutClose();
              onClose();
            }}
            onClose={flyoutMenu.handleFlyoutClose}
            onMouseEnter={flyoutMenu.handleFlyoutMouseEnter}
            onSuccess={onClose}
          />
          <SendToDeviceFlyoutMenu
            isOpen={sendFlyoutMenu.isFlyoutOpen}
            parentItemRef={sendFlyoutMenu.parentItemRef}
            books={[book]}
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
