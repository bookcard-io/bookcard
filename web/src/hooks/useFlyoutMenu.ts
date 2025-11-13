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

import { useCallback, useEffect, useRef, useState } from "react";

export interface UseFlyoutMenuOptions {
  /** Whether the parent menu is open. */
  parentMenuOpen: boolean;
}

export interface UseFlyoutMenuReturn {
  /** Whether the flyout menu is open. */
  isFlyoutOpen: boolean;
  /** Reference to the parent menu item element. */
  parentItemRef: React.RefObject<HTMLButtonElement | null>;
  /** Handle mouse entering the parent menu item. */
  handleParentMouseEnter: () => void;
  /** Handle mouse leaving the parent menu item. */
  handleParentMouseLeave: () => void;
  /** Handle mouse entering the flyout menu. */
  handleFlyoutMouseEnter: () => void;
  /** Handle closing the flyout menu. */
  handleFlyoutClose: () => void;
}

/**
 * Hook for managing flyout menu state.
 *
 * Handles opening/closing flyout menu based on hover interactions.
 * Follows SRP by managing only flyout menu state.
 * Follows IOC by accepting parent menu state as input.
 *
 * Parameters
 * ----------
 * options : UseFlyoutMenuOptions
 *     Configuration including parent menu open state.
 *
 * Returns
 * -------
 * UseFlyoutMenuReturn
 *     Flyout menu state and event handlers.
 */
export function useFlyoutMenu({
  parentMenuOpen,
}: UseFlyoutMenuOptions): UseFlyoutMenuReturn {
  const [isFlyoutOpen, setIsFlyoutOpen] = useState(false);
  const parentItemRef = useRef<HTMLButtonElement>(null);

  /**
   * Handle mouse entering the parent menu item.
   */
  const handleParentMouseEnter = useCallback(() => {
    setIsFlyoutOpen(true);
  }, []);

  /**
   * Handle mouse leaving the parent menu item.
   */
  const handleParentMouseLeave = useCallback(() => {
    // No-op: closing is managed by intent-aware guard in the flyout
  }, []);

  /**
   * Handle mouse entering the flyout menu.
   */
  const handleFlyoutMouseEnter = useCallback(() => {
    setIsFlyoutOpen(true);
  }, []);

  /**
   * Handle closing the flyout menu.
   */
  const handleFlyoutClose = useCallback(() => {
    setIsFlyoutOpen(false);
  }, []);

  // Close flyout when parent menu closes
  useEffect(() => {
    if (!parentMenuOpen) {
      setIsFlyoutOpen(false);
    }
  }, [parentMenuOpen]);

  return {
    isFlyoutOpen,
    parentItemRef,
    handleParentMouseEnter,
    handleParentMouseLeave,
    handleFlyoutMouseEnter,
    handleFlyoutClose,
  };
}
