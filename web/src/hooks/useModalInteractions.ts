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

export interface UseModalInteractionsOptions {
  /** Callback when modal should be closed (e.g., overlay click). */
  onClose: () => void;
}

export interface UseModalInteractionsResult {
  /** Handler for overlay click events. */
  handleOverlayClick: (e: React.MouseEvent<HTMLDivElement>) => void;
  /** Handler for modal click events (prevents propagation). */
  handleModalClick: (e: React.MouseEvent<HTMLDivElement>) => void;
  /** Handler for overlay keydown events (handles Escape key). */
  handleOverlayKeyDown: (e: React.KeyboardEvent<HTMLDivElement>) => void;
}

/**
 * Custom hook for modal interaction handlers.
 *
 * Provides standardized handlers for modal overlay and content interactions.
 * Follows SRP by focusing solely on modal interaction logic.
 * Follows DRY by centralizing common modal interaction patterns.
 * Uses IOC via callback dependencies.
 *
 * Parameters
 * ----------
 * options : UseModalInteractionsOptions
 *     Options containing the close callback.
 *
 * Returns
 * -------
 * UseModalInteractionsResult
 *     Object containing modal interaction handlers.
 */
export function useModalInteractions(
  options: UseModalInteractionsOptions,
): UseModalInteractionsResult {
  const { onClose } = options;

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose],
  );

  const handleModalClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      e.stopPropagation();
    },
    [],
  );

  const handleOverlayKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Escape") {
        onClose();
      }
    },
    [onClose],
  );

  return {
    handleOverlayClick,
    handleModalClick,
    handleOverlayKeyDown,
  };
}
