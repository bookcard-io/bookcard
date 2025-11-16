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
import { updateBookRating } from "@/services/bookService";

export interface UseBookRatingOptions {
  /** Function to optimistically update local book state. */
  onOptimisticUpdate: (bookId: number, rating: number | null) => void;
  /** Optional error handler. */
  onError?: (error: Error) => void;
}

export interface UseBookRatingResult {
  /** Function to update a book's rating. */
  updateRating: (bookId: number, rating: number | null) => Promise<void>;
}

/**
 * Custom hook for updating book ratings.
 *
 * Handles optimistic updates and API calls for rating changes.
 * Follows SRP by managing only rating update concerns.
 * Follows IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UseBookRatingOptions
 *     Configuration including optimistic update callback and error handler.
 *
 * Returns
 * -------
 * UseBookRatingResult
 *     Function to update book rating.
 */
export function useBookRating(
  options: UseBookRatingOptions,
): UseBookRatingResult {
  const { onOptimisticUpdate, onError } = options;

  const updateRating = useCallback(
    async (bookId: number, rating: number | null) => {
      // Optimistically update local state
      onOptimisticUpdate(bookId, rating);

      // Update via API
      try {
        await updateBookRating(bookId, rating);
      } catch (error) {
        // Error handling - could be enhanced with revert logic
        const errorMessage =
          error instanceof Error ? error : new Error("Unknown error");
        if (onError) {
          onError(errorMessage);
        } else {
          console.error("Error updating rating:", errorMessage);
        }
      }
    },
    [onOptimisticUpdate, onError],
  );

  return { updateRating };
}
