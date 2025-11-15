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

import { useCallback, useState } from "react";

export interface UseDeleteConfirmationStateReturn<T> {
  /** Whether the delete confirmation modal is open. */
  isOpen: boolean;
  /** Item to be deleted. */
  itemToDelete: T | null;
  /** Error message from delete operation. */
  error: string | null;
  /** Whether delete operation is in progress. */
  isDeleting: boolean;
  /** Open delete confirmation modal. */
  openDelete: (item: T) => void;
  /** Close delete confirmation modal and clear state. */
  close: () => void;
  /** Set error message. */
  setError: (error: string | null) => void;
  /** Set deleting state. */
  setIsDeleting: (isDeleting: boolean) => void;
}

/**
 * Hook for managing delete confirmation modal state.
 *
 * Handles delete confirmation modal visibility, selected item, error state,
 * and deletion progress. Follows SRP by focusing solely on delete confirmation state.
 * Follows DRY by centralizing delete confirmation patterns.
 * Follows IOC by providing callbacks for state changes.
 *
 * Parameters
 * ----------
 * T : type
 *     Type of the item being deleted.
 *
 * Returns
 * -------
 * UseDeleteConfirmationStateReturn<T>
 *     Object with delete confirmation state and handlers.
 */
export function useDeleteConfirmationState<
  T,
>(): UseDeleteConfirmationStateReturn<T> {
  const [isOpen, setIsOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const openDelete = useCallback((item: T) => {
    setItemToDelete(item);
    setError(null);
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    setItemToDelete(null);
    setError(null);
  }, []);

  return {
    isOpen,
    itemToDelete,
    error,
    isDeleting,
    openDelete,
    close,
    setError,
    setIsDeleting,
  };
}
