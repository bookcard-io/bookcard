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
import type { Shelf } from "@/types/shelf";

export interface UseShelfCardMenuActionsOptions {
  /** Shelf data. */
  shelf: Shelf;
  /** Callback when shelf is deleted successfully. */
  onShelfDeleted?: () => void;
  /** Callback when shelf deletion fails. */
  onDeleteError?: (error: string) => void;
}

export interface UseShelfCardMenuActionsResult {
  /** Handler for Delete action. */
  handleDelete: () => void;
}

/**
 * Custom hook for shelf card menu actions.
 *
 * Provides handlers for all menu actions.
 * Follows SRP by managing only menu action handlers.
 * Uses IOC via callback props.
 *
 * Parameters
 * ----------
 * options : UseShelfCardMenuActionsOptions
 *     Configuration including shelf data and callbacks.
 *
 * Returns
 * -------
 * UseShelfCardMenuActionsResult
 *     Menu action handlers.
 */
export function useShelfCardMenuActions({
  shelf: _shelf,
  onShelfDeleted,
  onDeleteError: _onDeleteError,
}: UseShelfCardMenuActionsOptions): UseShelfCardMenuActionsResult {
  const handleDelete = useCallback(() => {
    // Trigger deletion via callback
    onShelfDeleted?.();
  }, [onShelfDeleted]);

  return {
    handleDelete,
  };
}
