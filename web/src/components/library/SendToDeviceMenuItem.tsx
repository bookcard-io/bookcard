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

import { useMemo } from "react";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import { useUser } from "@/contexts/UserContext";
import type { Book } from "@/types/book";
import { buildBookPermissionContext } from "@/utils/permissions";

export interface SendToDeviceMenuItemProps {
  /** Reference to the menu item element. */
  itemRef: React.RefObject<HTMLButtonElement | null>;
  /** Callback when mouse enters the item. */
  onMouseEnter: () => void;
  /** Callback when mouse leaves the item. */
  onMouseLeave: () => void;
  /** Callback when item is clicked. */
  onClick?: () => void;
  /** Books to check permissions for. */
  books?: Book[];
  /** Whether the item is disabled (in addition to permission check). */
  disabled?: boolean;
}

/**
 * "Send to..." menu item component with flyout support.
 *
 * Displays a menu item that triggers a flyout menu on hover.
 * Handles permission checking internally to ensure consistency.
 * Follows SRP by handling menu item display, hover interactions, and permission checks.
 * Uses IOC via callback props for interactions.
 *
 * Parameters
 * ----------
 * props : SendToDeviceMenuItemProps
 *     Component props including refs, callbacks, and books for permission checking.
 */
export function SendToDeviceMenuItem({
  itemRef,
  onMouseEnter,
  onMouseLeave,
  onClick,
  books,
  disabled = false,
}: SendToDeviceMenuItemProps) {
  const { canPerformAction } = useUser();

  // Check permission - require ALL books to have permission
  // Errs on the side of disallowing if even one book lacks permission
  const canSend = useMemo(() => {
    if (!books || books.length === 0) {
      return false;
    }
    return books.every((book) =>
      canPerformAction("books", "send", buildBookPermissionContext(book)),
    );
  }, [books, canPerformAction]);

  // Item is disabled if user lacks permission OR explicitly disabled
  const isDisabled = !canSend || disabled;
  // Only allow click if user has permission
  const handleClick = canSend ? onClick : undefined;

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
        icon="pi pi-send"
        label="Send to..."
        onClick={handleClick}
        disabled={isDisabled}
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
