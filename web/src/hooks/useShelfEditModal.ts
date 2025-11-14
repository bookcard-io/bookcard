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
import type { Shelf, ShelfCreate, ShelfUpdate } from "@/types/shelf";

export interface UseShelfEditModalOptions {
  /** Shelf to edit. */
  shelf: Shelf;
  /** Callback fired when edit button is clicked (external edit handler). */
  onEdit?: (shelfId: number) => void;
  /** Handler for shelf update. */
  onShelfUpdate?: (shelf: Shelf) => Promise<void>;
  /** Handler for cover update (to refresh cover after upload/delete). */
  onCoverUpdate?: (shelfId: number, updatedShelf?: Shelf) => void;
}

export interface UseShelfEditModalResult {
  /** Whether edit modal is open. */
  showEditModal: boolean;
  /** Open edit modal. */
  openEditModal: () => void;
  /** Close edit modal. */
  closeEditModal: () => void;
  /** Handle edit button click. */
  handleEditClick: () => void;
  /** Handle shelf save. */
  handleShelfSave: (data: ShelfCreate | ShelfUpdate) => Promise<Shelf>;
  /** Handle cover saved callback. */
  handleCoverSaved: (updatedShelf: Shelf) => void;
  /** Handle cover deleted callback. */
  handleCoverDeleted: (updatedShelf: Shelf) => void;
}

/**
 * Custom hook for shelf edit modal management.
 *
 * Manages edit modal state and handlers for shelf editing.
 * Follows SRP by handling only edit modal concerns.
 * Follows IOC by accepting callbacks for operations.
 *
 * Parameters
 * ----------
 * options : UseShelfEditModalOptions
 *     Configuration options for edit modal.
 *
 * Returns
 * -------
 * UseShelfEditModalResult
 *     Object containing modal state and handlers.
 */
export function useShelfEditModal(
  options: UseShelfEditModalOptions,
): UseShelfEditModalResult {
  const { shelf, onEdit, onShelfUpdate, onCoverUpdate } = options;
  const [showEditModal, setShowEditModal] = useState(false);

  const handleEditClick = useCallback(() => {
    if (onEdit) {
      onEdit(shelf.id);
    } else {
      setShowEditModal(true);
    }
  }, [onEdit, shelf.id]);

  const handleShelfSave = useCallback(
    async (data: ShelfCreate | ShelfUpdate): Promise<Shelf> => {
      if (onShelfUpdate) {
        const updatedShelf = { ...shelf, ...data } as Shelf;
        await onShelfUpdate(updatedShelf);
        setShowEditModal(false);
        return updatedShelf;
      }
      setShowEditModal(false);
      return shelf;
    },
    [onShelfUpdate, shelf],
  );

  const handleCoverSaved = useCallback(
    (updatedShelf: Shelf) => {
      // Update cover in grid when cover is saved (O(1) operation)
      onCoverUpdate?.(updatedShelf.id, updatedShelf);
    },
    [onCoverUpdate],
  );

  const handleCoverDeleted = useCallback(
    (updatedShelf: Shelf) => {
      // Update cover in grid when cover is deleted (O(1) operation)
      onCoverUpdate?.(updatedShelf.id, updatedShelf);
    },
    [onCoverUpdate],
  );

  return {
    showEditModal,
    openEditModal: () => setShowEditModal(true),
    closeEditModal: () => setShowEditModal(false),
    handleEditClick,
    handleShelfSave,
    handleCoverSaved,
    handleCoverDeleted,
  };
}
