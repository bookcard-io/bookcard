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

import type { AuthorWithMetadata } from "@/types/author";
import { normalizeAuthorKey } from "./openLibrary";

/**
 * Author utility functions.
 *
 * Provides utilities for working with author data.
 * Follows SRP by focusing solely on author-related operations.
 */

/**
 * Build the author identifier used for rematch requests.
 *
 * The backend prefers a Calibre-based identifier so it can always
 * resolve or create the appropriate mapping, regardless of whether
 * the author is already matched:
 *
 * - If `calibre_id` is present, use `calibre-{calibre_id}`.
 * - Otherwise, fall back to an existing `calibre-` style key.
 * - As a last resort, use a normalized OpenLibrary key.
 *
 * Parameters
 * ----------
 * author : AuthorWithMetadata
 *     Author data to extract identifier from.
 *
 * Returns
 * -------
 * string | null
 *     Author identifier for rematch, or null if not available.
 */
export function buildRematchAuthorId(
  author: AuthorWithMetadata,
): string | null {
  if (author.calibre_id != null) {
    return `calibre-${author.calibre_id}`;
  }

  if (author.key?.startsWith("calibre-")) {
    return author.key;
  }

  const normalizedKey = normalizeAuthorKey(author.key);
  return normalizedKey || null;
}
