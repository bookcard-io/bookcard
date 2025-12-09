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
import { useShelvesContext } from "@/contexts/ShelvesContext";
import type { CreateShelfOptions } from "@/services/shelfService";
import {
  createShelf as createShelfApi,
  deleteShelf,
  updateShelf as updateShelfApi,
} from "@/services/shelfService";
import type { Shelf, ShelfCreate, ShelfUpdate } from "@/types/shelf";

export interface ShelfDataUpdateRef {
  /** Update shelf data in local state. */
  updateShelf: (shelfId: number, shelfData: Partial<Shelf>) => void;
  /** Update cover with cache-busting. */
  updateCover: (shelfId: number) => void;
}

export interface UseShelfGridOperationsOptions {
  /** Ref for shelf data updates (from useShelfDataUpdates). */
  shelfDataUpdateRef: React.RefObject<ShelfDataUpdateRef>;
  /** Callback to remove shelves from selection after deletion. */
  onShelvesDeleted?: (shelfIds: number[]) => void;
  /** Callback when operation fails. */
  onError?: (error: Error) => void;
}

export interface UseShelfGridOperationsResult {
  /** Handle shelf update. */
  handleShelfUpdate: (shelf: Shelf) => Promise<void>;
  /** Handle cover update (for refreshing cover after upload/delete). */
  handleCoverUpdate: (shelfId: number, updatedShelf?: Shelf) => void;
  /** Handle shelf deletion (single or multiple). */
  handleShelfDelete: (shelfIds: number | number[]) => Promise<void>;
  /** Handle shelf creation. */
  handleCreateShelf: (
    data: ShelfCreate | ShelfUpdate,
    options?: CreateShelfOptions,
  ) => Promise<Shelf>;
}

/**
 * Custom hook for shelf grid operations (CRUD).
 *
 * Handles shelf update, delete, create, and cover update operations.
 * Follows SRP by handling only shelf operation concerns.
 * Follows IOC by accepting callbacks and refs.
 *
 * Parameters
 * ----------
 * options : UseShelfGridOperationsOptions
 *     Configuration options for operations.
 *
 * Returns
 * -------
 * UseShelfGridOperationsResult
 *     Object containing operation handlers.
 */
export function useShelfGridOperations(
  options: UseShelfGridOperationsOptions,
): UseShelfGridOperationsResult {
  const { shelfDataUpdateRef, onShelvesDeleted, onError } = options;
  const { refresh: refreshContext } = useShelvesContext();

  const handleShelfUpdate = useCallback(
    async (shelf: Shelf) => {
      await updateShelfApi(shelf.id, {
        name: shelf.name,
        description: shelf.description,
        is_public: shelf.is_public,
      });
      // Refresh context to sync with Sidebar and other components
      await refreshContext();
      // Update local state to reflect changes without full refresh
      shelfDataUpdateRef.current?.updateShelf(shelf.id, {
        name: shelf.name,
        description: shelf.description,
        is_public: shelf.is_public,
      });
    },
    [refreshContext, shelfDataUpdateRef],
  );

  const handleCoverUpdate = useCallback(
    (shelfId: number, updatedShelf?: Shelf) => {
      if (updatedShelf) {
        // Update shelf data with the actual updated shelf from API
        shelfDataUpdateRef.current?.updateShelf(shelfId, {
          cover_picture: updatedShelf.cover_picture,
        });
      } else {
        // Fallback: just trigger cover refresh with cache-busting
        shelfDataUpdateRef.current?.updateCover(shelfId);
      }
    },
    [shelfDataUpdateRef],
  );

  const handleShelfDelete = useCallback(
    async (shelfIds: number | number[]) => {
      const idsToDelete = Array.isArray(shelfIds) ? shelfIds : [shelfIds];

      try {
        // Delete all shelves in parallel
        await Promise.all(idsToDelete.map((id) => deleteShelf(id)));

        // Remove deleted shelves from selection
        onShelvesDeleted?.(idsToDelete);

        // Refresh context to sync with Sidebar and other components
        await refreshContext();
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));
        console.error("Failed to delete shelf(s):", err);
        onError?.(err);
        throw err;
      }
    },
    [refreshContext, onShelvesDeleted, onError],
  );

  const handleCreateShelf = useCallback(
    async (
      data: ShelfCreate | ShelfUpdate,
      options?: CreateShelfOptions,
    ): Promise<Shelf> => {
      const newShelf = await (options
        ? createShelfApi(data as ShelfCreate, options)
        : createShelfApi(data as ShelfCreate));
      // Refresh context to sync with Sidebar and other components
      await refreshContext();
      return newShelf;
    },
    [refreshContext],
  );

  return {
    handleShelfUpdate,
    handleCoverUpdate,
    handleShelfDelete,
    handleCreateShelf,
  };
}
