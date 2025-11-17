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
import type { Shelf } from "@/types/shelf";
import { buildShelfPermissionContext } from "@/utils/permissions";

export interface ShelfCardMenuProps {
  /** Whether the menu is open. */
  isOpen: boolean;
  /** Callback when menu should be closed. */
  onClose: () => void;
  /** Reference to the button element (for click outside detection). */
  buttonRef: React.RefObject<HTMLElement | null>;
  /** Cursor position when menu was opened. */
  cursorPosition: { x: number; y: number } | null;
  /** Callback when Delete is clicked. */
  onDelete?: () => void;
  /** Shelf object for permission checking. */
  shelf: Shelf;
}

/**
 * Shelf card context menu component.
 *
 * Displays a dropdown menu with shelf actions.
 * Follows SRP by handling only menu display and item selection.
 * Uses IOC via callback props for actions.
 * Follows DRY by using shared DropdownMenu and DropdownMenuItem components.
 */
export function ShelfCardMenu({
  isOpen,
  onClose,
  buttonRef,
  cursorPosition,
  onDelete,
  shelf,
}: ShelfCardMenuProps) {
  const { canPerformAction } = useUser();
  const shelfContext = buildShelfPermissionContext(shelf);
  const canDelete = canPerformAction("shelves", "delete", shelfContext);

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

  return (
    <DropdownMenu
      isOpen={isOpen}
      onClose={onClose}
      buttonRef={buttonRef}
      cursorPosition={cursorPosition}
      ariaLabel="Shelf actions"
    >
      <DropdownMenuItem
        icon="pi pi-trash"
        label="Delete"
        onClick={canDelete ? () => handleItemClick(onDelete) : undefined}
        disabled={!canDelete}
      />
    </DropdownMenu>
  );
}
