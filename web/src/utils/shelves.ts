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

/**
 * Shelf-related utility functions.
 *
 * Provides reusable functions for shelf data manipulation.
 * Follows SRP by separating shelf manipulation logic from presentation.
 * Follows DRY by centralizing shelf-related utilities.
 */

import { getShelfCoverPictureUrl } from "@/services/shelfService";
import type { Shelf } from "@/types/shelf";

/**
 * Generate cache-busting cover URL for a shelf.
 *
 * Parameters
 * ----------
 * shelfId : number
 *     Shelf ID.
 * cacheBuster? : number
 *     Optional cache-busting timestamp. Defaults to current time.
 *
 * Returns
 * -------
 * string
 *     Cover URL with cache-busting parameter.
 */
export function getShelfCoverUrlWithCacheBuster(
  shelfId: number,
  cacheBuster?: number,
): string {
  const baseUrl = getShelfCoverPictureUrl(shelfId);
  const timestamp = cacheBuster ?? Date.now();
  return `${baseUrl}?v=${timestamp}`;
}

/**
 * Deduplicate shelves by ID and apply shelf data overrides.
 *
 * Removes duplicate shelves based on ID and optionally applies
 * shelf data overrides from a map (including cover picture).
 * Only creates new objects for shelves with overrides to optimize performance.
 *
 * Parameters
 * ----------
 * shelves : Shelf[]
 *     Array of shelves to deduplicate.
 * shelfDataOverrides? : Map<number, Partial<Shelf>>
 *     Optional map of shelf ID to override shelf data (name, cover_picture, etc.).
 *
 * Returns
 * -------
 * Shelf[]
 *     Deduplicated array of shelves with overrides applied.
 */
export function deduplicateShelves(
  shelves: Shelf[],
  shelfDataOverrides?: Map<number, Partial<Shelf>>,
): Shelf[] {
  const seen = new Set<number>();
  const result: Shelf[] = [];

  for (const shelf of shelves) {
    if (seen.has(shelf.id)) {
      continue;
    }
    seen.add(shelf.id);

    // Check for overrides (Map lookups are O(1))
    const overrideData = shelfDataOverrides?.get(shelf.id);

    // Only create new object if there are overrides
    if (overrideData) {
      const updatedShelf = { ...shelf };
      Object.assign(updatedShelf, overrideData);
      result.push(updatedShelf);
    } else {
      result.push(shelf);
    }
  }

  return result;
}

/**
 * Sort shelves by created_at in descending order (newest first).
 *
 * Parameters
 * ----------
 * shelves : Shelf[]
 *     Array of shelves to sort.
 *
 * Returns
 * -------
 * Shelf[]
 *     Sorted array of shelves.
 */
export function sortShelvesByCreatedAt(shelves: Shelf[]): Shelf[] {
  return [...shelves].sort((a, b) => {
    const dateA = new Date(a.created_at).getTime();
    const dateB = new Date(b.created_at).getTime();
    return dateB - dateA; // Descending order
  });
}

/**
 * Process shelves: deduplicate, apply overrides, and sort.
 *
 * Combines deduplication, override application, and sorting into a single operation.
 * Follows DRY by centralizing shelf data transformation logic.
 *
 * Parameters
 * ----------
 * shelves : Shelf[]
 *     Array of shelves to process.
 * shelfDataOverrides? : Map<number, Partial<Shelf>>
 *     Optional map of shelf ID to override shelf data.
 *
 * Returns
 * -------
 * Shelf[]
 *     Processed array of shelves (deduplicated, overridden, sorted).
 */
export function processShelves(
  shelves: Shelf[],
  shelfDataOverrides?: Map<number, Partial<Shelf>>,
): Shelf[] {
  const deduplicated = deduplicateShelves(shelves, shelfDataOverrides);
  return sortShelvesByCreatedAt(deduplicated);
}
