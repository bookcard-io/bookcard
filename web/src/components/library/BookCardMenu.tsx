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
import { LibraryBuilding } from "@/icons/LibraryBuilding";
import { InterfaceContentBook2LibraryContentBooksBookShelfStack as Shelf } from "@/icons/Shelf";
import { cn } from "@/libs/utils";

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
 * Follows DRY by using shared DropdownMenu and DropdownMenuItem components.
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
  const handleItemClick = useCallback(
    (handler?: () => void) => {
      if (handler) {
        handler();
      }
      onClose();
    },
    [onClose],
  );

  return (
    <DropdownMenu
      isOpen={isOpen}
      onClose={onClose}
      buttonRef={buttonRef}
      cursorPosition={cursorPosition}
      ariaLabel="Book actions"
    >
      <DropdownMenuItem
        icon="pi pi-info-circle"
        label="Book info"
        onClick={() => handleItemClick(onBookInfo)}
      />
      <DropdownMenuItem
        icon="pi pi-send"
        label="Send"
        onClick={() => handleItemClick(onSend)}
      />
      <DropdownMenuItem
        icon={<LibraryBuilding className="h-4 w-4" />}
        label="Move to library"
        onClick={() => handleItemClick(onMoveToLibrary)}
      />
      <DropdownMenuItem
        icon={<Shelf className="h-4 w-4" />}
        label="Add to shelf"
        onClick={() => handleItemClick(onMoveToShelf)}
      />
      <DropdownMenuItem
        icon="pi pi-arrow-right-arrow-left"
        label="Convert format"
        onClick={() => handleItemClick(onConvert)}
      />
      <DropdownMenuItem
        icon="pi pi-trash"
        label="Delete"
        onClick={() => handleItemClick(onDelete)}
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
  );
}
