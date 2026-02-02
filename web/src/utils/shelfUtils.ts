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
 * Shelf-specific helpers that are safe to import from both services and UI.
 *
 * Notes
 * -----
 * This module intentionally does not import from `@/services/*` to avoid circular
 * dependencies (e.g. `utils/shelves.ts` already imports `services/shelfService`).
 */

export interface ShelfLike {
  shelf_type?: unknown;
}

/**
 * Get a normalized shelf type string.
 *
 * Parameters
 * ----------
 * shelf : ShelfLike
 *     Shelf-like object that may contain a `shelf_type`.
 *
 * Returns
 * -------
 * string
 *     Lowercased shelf type, or empty string if unavailable.
 */
export function getShelfType(shelf: ShelfLike): string {
  const raw = shelf.shelf_type;
  return typeof raw === "string" ? raw.toLowerCase() : "";
}

/**
 * Check whether a shelf is a Magic Shelf.
 *
 * Parameters
 * ----------
 * shelf : ShelfLike
 *     Shelf-like object.
 *
 * Returns
 * -------
 * boolean
 *     True if the shelf type is `magic_shelf`.
 */
export function isMagicShelf(shelf: ShelfLike): boolean {
  return getShelfType(shelf) === "magic_shelf";
}

export interface ShelfBooksPreviewResponse {
  book_ids?: unknown;
}

/**
 * Type guard for shelf book-list responses that may include `book_ids`.
 *
 * The backend has historically returned either a raw list of IDs, or an object
 * with `book_ids`. This helper supports both.
 */
export function isShelfBooksPreviewResponse(
  data: unknown,
): data is ShelfBooksPreviewResponse {
  return typeof data === "object" && data !== null;
}

/**
 * Extract book IDs from either `number[]` or `{ book_ids: number[] }` responses.
 *
 * Parameters
 * ----------
 * data : unknown
 *     JSON-decoded response body.
 *
 * Returns
 * -------
 * number[]
 *     Sanitized list of numeric book IDs.
 */
export function extractShelfBookIds(data: unknown): number[] {
  if (Array.isArray(data)) {
    return data.filter((id): id is number => typeof id === "number");
  }

  if (!isShelfBooksPreviewResponse(data)) {
    return [];
  }

  const maybe = data as { book_ids?: unknown };
  if (!Array.isArray(maybe.book_ids)) {
    return [];
  }

  return maybe.book_ids.filter((id): id is number => typeof id === "number");
}
