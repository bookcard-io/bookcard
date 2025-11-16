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

import { useCallback } from "react";
import type { UseFlyoutMenuReturn } from "./useFlyoutMenu";

export interface UseExclusiveFlyoutMenusReturn {
  /**
   * Wrapped mouse enter handler for the first flyout menu.
   * Closes the second flyout if open, then opens the first.
   */
  handleFirstMouseEnter: () => void;
  /**
   * Wrapped mouse enter handler for the second flyout menu.
   * Closes the first flyout if open, then opens the second.
   */
  handleSecondMouseEnter: () => void;
}

/**
 * Hook for managing mutually exclusive flyout menus.
 *
 * Ensures only one flyout menu can be open at a time by closing
 * the other when one opens. This prevents multiple flyouts from
 * being open simultaneously, which is especially important on mobile.
 *
 * Follows SRP by managing only flyout exclusivity logic.
 * Follows IOC by accepting flyout menu instances as dependencies.
 *
 * Parameters
 * ----------
 * firstFlyout : UseFlyoutMenuReturn
 *     First flyout menu instance.
 * secondFlyout : UseFlyoutMenuReturn
 *     Second flyout menu instance.
 *
 * Returns
 * -------
 * UseExclusiveFlyoutMenusReturn
 *     Wrapped mouse enter handlers that ensure mutual exclusivity.
 */
export function useExclusiveFlyoutMenus(
  firstFlyout: UseFlyoutMenuReturn,
  secondFlyout: UseFlyoutMenuReturn,
): UseExclusiveFlyoutMenusReturn {
  /**
   * Handle first flyout menu item mouse enter.
   * Closes the second flyout if open, then opens the first.
   */
  const handleFirstMouseEnter = useCallback(() => {
    // Close the other flyout if it's open
    if (secondFlyout.isFlyoutOpen) {
      secondFlyout.handleFlyoutClose();
    }
    // Open this flyout
    firstFlyout.handleParentMouseEnter();
  }, [firstFlyout, secondFlyout]);

  /**
   * Handle second flyout menu item mouse enter.
   * Closes the first flyout if open, then opens the second.
   */
  const handleSecondMouseEnter = useCallback(() => {
    // Close the other flyout if it's open
    if (firstFlyout.isFlyoutOpen) {
      firstFlyout.handleFlyoutClose();
    }
    // Open this flyout
    secondFlyout.handleParentMouseEnter();
  }, [firstFlyout, secondFlyout]);

  return {
    handleFirstMouseEnter,
    handleSecondMouseEnter,
  };
}
