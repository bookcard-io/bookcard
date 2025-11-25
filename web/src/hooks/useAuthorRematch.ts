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
import { rematchAuthor } from "@/services/authorService";
import type { AuthorWithMetadata } from "@/types/author";
import { buildRematchAuthorId } from "@/utils/author";

export interface UseAuthorRematchOptions {
  /** Author to rematch. */
  author: AuthorWithMetadata;
  /** Callback when rematch succeeds with new OpenLibrary key. */
  onRematchSuccess?: (openlibraryKey: string) => void;
  /** Callback when rematch fails. */
  onRematchError?: (error: Error) => void;
}

export interface UseAuthorRematchResult {
  /** Whether rematch is in progress. */
  isRematching: boolean;
  /** Rematch the author with optional OpenLibrary key. */
  rematch: (openlibraryKey?: string) => Promise<void>;
}

/**
 * Custom hook for author rematch functionality.
 *
 * Handles author rematch API calls and state management.
 * Follows SRP by managing only rematch concerns.
 * Follows IOC by accepting callbacks and returning state/actions.
 *
 * Parameters
 * ----------
 * options : UseAuthorRematchOptions
 *     Hook options including author and callbacks.
 *
 * Returns
 * -------
 * UseAuthorRematchResult
 *     Rematch state and function.
 */
export function useAuthorRematch(
  options: UseAuthorRematchOptions,
): UseAuthorRematchResult {
  const { author, onRematchSuccess, onRematchError } = options;
  const [isRematching, setIsRematching] = useState(false);

  const rematch = useCallback(
    async (openlibraryKey?: string): Promise<void> => {
      const authorIdForRematch = buildRematchAuthorId(author);
      if (isRematching || !authorIdForRematch) {
        return;
      }

      setIsRematching(true);
      try {
        const result = await rematchAuthor(authorIdForRematch, openlibraryKey);

        // If we have the new OpenLibrary key, notify success callback
        if (result.openlibrary_key) {
          onRematchSuccess?.(result.openlibrary_key);
        }
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));
        console.error("Failed to rematch author:", err);
        onRematchError?.(err);
        // TODO: Show error toast/notification
      } finally {
        setIsRematching(false);
      }
    },
    [author, isRematching, onRematchSuccess, onRematchError],
  );

  return { isRematching, rematch };
}
