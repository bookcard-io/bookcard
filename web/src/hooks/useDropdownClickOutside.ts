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

import { useEffect } from "react";

export interface UseDropdownClickOutsideOptions {
  /** Whether the menu is open. */
  isOpen: boolean;
  /** Reference to the button element (excluded from click outside). */
  buttonRef: React.RefObject<HTMLElement | null>;
  /** Reference to the menu element (excluded from click outside). */
  menuRef: React.RefObject<HTMLElement | null>;
  /** Callback when click outside is detected. */
  onClose: () => void;
}

/**
 * Custom hook for detecting clicks outside dropdown menu.
 *
 * Handles click outside detection while excluding both the button
 * and menu elements from triggering the close action.
 * Follows SRP by handling only click outside detection logic.
 * Follows IOC by accepting refs and callback as inputs.
 *
 * Parameters
 * ----------
 * options : UseDropdownClickOutsideOptions
 *     Configuration including open state, refs, and close callback.
 */
export function useDropdownClickOutside({
  isOpen,
  buttonRef,
  menuRef,
  onClose,
}: UseDropdownClickOutsideOptions): void {
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
  }, [isOpen, buttonRef, menuRef, onClose]);
}
