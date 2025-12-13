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
 * Centralized React Query key registry for books and reading-related queries.
 *
 * This module provides a single source of truth for all query keys used
 * throughout the application, following the Open/Closed Principle by
 * allowing new query keys to be added without modifying existing code.
 */

/**
 * Query keys for book list queries (paginated).
 */
export const bookListQueryKeys = ["books", "filtered-books"] as const;

/**
 * Query keys for infinite book list queries.
 */
export const bookInfiniteQueryKeys = [
  "books-infinite",
  "filtered-books-infinite",
] as const;

/**
 * Query key factory for read status queries.
 *
 * Parameters
 * ----------
 * bookId : number
 *     Book ID to create query key for.
 *
 * Returns
 * -------
 * readonly [string, number]
 *     Query key tuple for the read status query.
 */
export const readStatusQueryKey = (bookId: number) =>
  ["read-status", bookId] as const;

/**
 * Base query key for read status queries (used for invalidation).
 */
export const readStatusBaseQueryKey = ["read-status"] as const;

/**
 * Query key for recent reads list.
 */
export const recentReadsQueryKey = ["recent-reads"] as const;
