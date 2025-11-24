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

import type { Book } from "epubjs";

/**
 * EPUB location utilities.
 *
 * Centralized location and progress calculation logic.
 * Follows SRP by separating location logic from rendering components.
 * Follows DRY by eliminating location calculation duplication.
 */

/**
 * EPUB locations type extracted from Book interface.
 */
type EpubLocations = NonNullable<Book["locations"]>;

/**
 * Get total number of locations from a book.
 *
 * Parameters
 * ----------
 * locations : EpubLocations | null | undefined
 *     EPUB locations object.
 *
 * Returns
 * -------
 * number
 *     Total number of locations, or 0 if unavailable.
 */
export function getTotalLocations(
  locations: EpubLocations | null | undefined,
): number {
  if (!locations) {
    return 0;
  }

  const locationsLength =
    typeof (locations as unknown as { length: () => number }).length ===
    "function"
      ? (locations as unknown as { length: () => number }).length()
      : (locations as unknown as { length?: number }).length;

  return locationsLength || 0;
}

/**
 * Check if locations are ready (generated/cached).
 *
 * Parameters
 * ----------
 * locations : EpubLocations | null | undefined
 *     EPUB locations object.
 *
 * Returns
 * -------
 * boolean
 *     True if locations are ready, false otherwise.
 */
export function areLocationsReady(
  locations: EpubLocations | null | undefined,
): boolean {
  if (!locations) {
    return false;
  }
  return (locations as unknown as { total?: number }).total !== undefined;
}

/**
 * Calculate reading progress from CFI location.
 *
 * Parameters
 * ----------
 * book : Book | null
 *     EPUB book object.
 * cfi : string
 *     CFI location string.
 *
 * Returns
 * -------
 * number
 *     Progress value between 0.0 and 1.0, or 0 if calculation fails.
 */
export function calculateProgressFromCfi(
  book: Book | null,
  cfi: string,
): number {
  if (!book?.locations) {
    return 0;
  }

  try {
    const currentLocation = book.locations.locationFromCfi(cfi);
    const totalLocations = getTotalLocations(book.locations);

    if (totalLocations > 0 && typeof currentLocation === "number") {
      return Math.min(1, Math.max(0, currentLocation / totalLocations));
    }
  } catch {
    // Fallback to 0 if calculation fails
  }

  return 0;
}

/**
 * Get CFI location from progress value.
 *
 * Parameters
 * ----------
 * book : Book | null
 *     EPUB book object.
 * progress : number
 *     Progress value between 0.0 and 1.0.
 *
 * Returns
 * -------
 * string | null
 *     CFI location string, or null if unavailable.
 */
export function getCfiFromProgress(
  book: Book | null,
  progress: number,
): string | null {
  if (!book?.locations) {
    return null;
  }

  const totalLocations = getTotalLocations(book.locations);
  if (totalLocations === 0) {
    return null;
  }

  const clampedProgress = Math.min(1, Math.max(0, progress));
  const targetLocation =
    clampedProgress >= 1.0
      ? totalLocations - 1
      : Math.floor(clampedProgress * totalLocations);

  const safeTargetLocation = Math.min(
    targetLocation,
    Math.max(0, totalLocations - 1),
  );

  try {
    return book.locations.cfiFromLocation(safeTargetLocation) || null;
  } catch {
    return null;
  }
}
