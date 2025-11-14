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
import {
  deleteShelfCoverPicture,
  uploadShelfCoverPicture,
} from "@/services/shelfService";
import type { Shelf } from "@/types/shelf";

export interface ShelfCoverOperations {
  /** Upload cover picture for a shelf. */
  uploadCover: (shelfId: number, file: File) => Promise<Shelf>;
  /** Delete cover picture for a shelf. */
  deleteCover: (shelfId: number) => Promise<Shelf>;
}

export interface UseShelfCoverOperationsOptions {
  /** Custom cover operations (for IOC/testing). Defaults to service functions. */
  operations?: ShelfCoverOperations;
  /** Callback when cover is successfully uploaded. */
  onCoverSaved?: (shelf: Shelf) => void;
  /** Callback when cover is successfully deleted. */
  onCoverDeleted?: (shelf: Shelf) => void;
  /** Callback when cover operation fails. */
  onError?: (error: string) => void;
}

export interface UseShelfCoverOperationsResult {
  /** Execute cover operations (upload/delete) for a saved shelf. */
  executeCoverOperations: (
    shelf: Shelf,
    coverFile: File | null,
    isCoverDeleteStaged: boolean,
  ) => Promise<void>;
}

/**
 * Custom hook for shelf cover operations.
 *
 * Handles cover upload and deletion operations with error handling.
 * Follows SRP by handling only cover operation concerns.
 * Follows IOC by accepting custom operations and callbacks.
 *
 * Parameters
 * ----------
 * options : UseShelfCoverOperationsOptions
 *     Configuration options for cover operations.
 *
 * Returns
 * -------
 * UseShelfCoverOperationsResult
 *     Object containing cover operation executor.
 */
export function useShelfCoverOperations(
  options: UseShelfCoverOperationsOptions = {},
): UseShelfCoverOperationsResult {
  const { operations, onCoverSaved, onCoverDeleted, onError } = options;

  const uploadCover = operations?.uploadCover ?? uploadShelfCoverPicture;
  const deleteCover = operations?.deleteCover ?? deleteShelfCoverPicture;

  const executeCoverOperations = useCallback(
    async (
      shelf: Shelf,
      coverFile: File | null,
      isCoverDeleteStaged: boolean,
    ): Promise<void> => {
      // Delete cover if deletion is staged
      if (isCoverDeleteStaged) {
        try {
          const updatedShelf = await deleteCover(shelf.id);
          onCoverDeleted?.(updatedShelf);
        } catch (error) {
          const errorMessage =
            error instanceof Error
              ? error.message
              : "Failed to delete cover picture";
          onError?.(errorMessage);
          throw error;
        }
      }

      // Upload cover picture if one was selected
      if (coverFile) {
        try {
          const updatedShelf = await uploadCover(shelf.id, coverFile);
          onCoverSaved?.(updatedShelf);
        } catch (error) {
          const errorMessage =
            error instanceof Error
              ? error.message
              : "Failed to upload cover picture";
          onError?.(errorMessage);
          throw error;
        }
      }
    },
    [uploadCover, deleteCover, onCoverSaved, onCoverDeleted, onError],
  );

  return {
    executeCoverOperations,
  };
}
