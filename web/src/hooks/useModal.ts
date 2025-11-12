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

/**
 * Custom hook for modal behavior.
 *
 * Manages body scroll lock when modal is open.
 * Follows SRP by focusing solely on modal lifecycle management.
 *
 * Parameters
 * ----------
 * isOpen : boolean
 *     Whether the modal is open.
 */
export function useModal(isOpen: boolean): void {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = "auto";
      };
    }
    return undefined;
  }, [isOpen]);
}
