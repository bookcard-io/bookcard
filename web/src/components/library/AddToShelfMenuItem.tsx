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

import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import { InterfaceContentBook2LibraryContentBooksBookShelfStack as Shelf } from "@/icons/Shelf";

export interface AddToShelfMenuItemProps {
  /** Reference to the menu item element. */
  itemRef: React.RefObject<HTMLButtonElement>;
  /** Callback when mouse enters the item. */
  onMouseEnter: () => void;
  /** Callback when mouse leaves the item. */
  onMouseLeave: () => void;
  /** Callback when item is clicked. */
  onClick?: () => void;
}

/**
 * "Add to..." menu item component with flyout support.
 *
 * Displays a menu item that triggers a flyout menu on hover.
 * Follows SRP by handling only menu item display and hover interactions.
 * Uses IOC via callback props for interactions.
 *
 * Parameters
 * ----------
 * props : AddToShelfMenuItemProps
 *     Component props including refs and callbacks.
 */
export function AddToShelfMenuItem({
  itemRef,
  onMouseEnter,
  onMouseLeave,
  onClick,
}: AddToShelfMenuItemProps) {
  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: hover wrapper for flyout menu */
    <div
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      className="relative"
      role="presentation"
    >
      <DropdownMenuItem
        ref={itemRef}
        icon={<Shelf className="h-4 w-4" />}
        label="Add to..."
        onClick={onClick}
        rightContent={
          <i
            className="pi pi-chevron-right flex-shrink-0 text-xs"
            aria-hidden="true"
          />
        }
        justifyBetween
      />
    </div>
  );
}
