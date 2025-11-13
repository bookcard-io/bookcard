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
import { useShelvesContext } from "@/contexts/ShelvesContext";
import { useRecentShelves } from "@/hooks/useRecentShelves";
import { useShelfActions } from "@/hooks/useShelfActions";
import { createShelf as createShelfService } from "@/services/shelfService";
import type { Shelf, ShelfCreate, ShelfUpdate } from "@/types/shelf";

export interface UseCreateShelfWithBookOptions {
  /** Book ID to add to the newly created shelf. */
  bookId: number;
  /** Callback when shelf creation is successful. */
  onSuccess?: () => void;
  /** Callback when shelf creation fails. */
  onError?: (error: unknown) => void;
}

export interface UseCreateShelfWithBookReturn {
  /** Whether the create shelf modal should be shown. */
  showCreateModal: boolean;
  /** Open the create shelf modal. */
  openCreateModal: () => void;
  /** Close the create shelf modal. */
  closeCreateModal: () => void;
  /** Handle shelf creation with book addition. */
  handleCreateShelf: (data: ShelfCreate | ShelfUpdate) => Promise<Shelf>;
}

/**
 * Hook for creating a shelf and adding a book to it.
 *
 * Manages shelf creation modal state and handles the workflow of creating
 * a shelf and adding a book to it. Follows SRP by handling only shelf
 * creation with book addition logic. Follows IOC by accepting callbacks.
 * Follows DRY by centralizing this common workflow.
 *
 * Parameters
 * ----------
 * options : UseCreateShelfWithBookOptions
 *     Configuration including book ID and callbacks.
 *
 * Returns
 * -------
 * UseCreateShelfWithBookReturn
 *     Modal state and creation handler.
 */
export function useCreateShelfWithBook({
  bookId,
  onSuccess,
  onError,
}: UseCreateShelfWithBookOptions): UseCreateShelfWithBookReturn {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const { addBook } = useShelfActions();
  const { addRecentShelf } = useRecentShelves();
  const { refresh: refreshShelvesContext } = useShelvesContext();

  /**
   * Open the create shelf modal.
   */
  const openCreateModal = useCallback(() => {
    setShowCreateModal(true);
  }, []);

  /**
   * Close the create shelf modal.
   */
  const closeCreateModal = useCallback(() => {
    setShowCreateModal(false);
  }, []);

  /**
   * Handle shelf creation with book addition.
   *
   * Parameters
   * ----------
   * data : ShelfCreate | ShelfUpdate
   *     Shelf creation data.
   */
  const handleCreateShelf = useCallback(
    async (data: ShelfCreate | ShelfUpdate): Promise<Shelf> => {
      try {
        const newShelf = await createShelfService(data as ShelfCreate);
        // Add book to the newly created shelf
        await addBook(newShelf.id, bookId);
        // Add to recent shelves
        addRecentShelf(newShelf.id);
        // Refresh shelves context
        await refreshShelvesContext();
        setShowCreateModal(false);
        onSuccess?.();
        return newShelf;
      } catch (error) {
        console.error("Failed to create shelf and add book:", error);
        onError?.(error);
        // Modal will stay open to show error
        throw error;
      }
    },
    [
      addBook,
      bookId,
      addRecentShelf,
      refreshShelvesContext,
      onSuccess,
      onError,
    ],
  );

  return {
    showCreateModal,
    openCreateModal,
    closeCreateModal,
    handleCreateShelf,
  };
}
