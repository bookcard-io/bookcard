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
 * OpenLibrary utility functions.
 *
 * Provides utilities for working with OpenLibrary identifiers and keys.
 * Follows SRP by focusing solely on OpenLibrary-related operations.
 */

/**
 * Normalize an OpenLibrary author key to a bare OLID.
 *
 * Examples
 * --------
 * - "/authors/OL52940A" -> "OL52940A"
 * - "authors/OL52940A" -> "OL52940A"
 * - "OL52940A" -> "OL52940A"
 *
 * Parameters
 * ----------
 * key : string | null | undefined
 *     The OpenLibrary key to normalize.
 *
 * Returns
 * -------
 * string
 *     Normalized OLID, or empty string if key is null/undefined.
 */
export function normalizeAuthorKey(key?: string | null): string {
  return key?.replace(/^\/?authors\//, "").replace(/^\//, "") ?? "";
}

/**
 * Validates an OpenLibrary ID (OLID) format.
 *
 * OpenLibrary author keys follow the pattern: OL[0-9]+[A-Z]
 * Examples: OL23919A, OL676009W, /authors/OL23919A
 *
 * Parameters
 * ----------
 * olid : string
 *     The OLID to validate (may include /authors/ prefix).
 *
 * Returns
 * -------
 * { isValid: boolean; error?: string }
 *     Validation result with optional error message.
 */
export function validateOlid(olid: string): {
  isValid: boolean;
  error?: string;
} {
  const trimmed = olid.trim();
  if (!trimmed) {
    return { isValid: false, error: "OLID cannot be empty" };
  }

  // Remove /authors/ prefix if present for validation
  const normalized = trimmed.replace(/^\/?authors\//, "").replace(/^\//, "");

  // OpenLibrary keys follow pattern: OL followed by digits, then a letter
  // Examples: OL23919A, OL676009W
  const olidPattern = /^OL\d+[A-Z]$/i;

  if (!olidPattern.test(normalized)) {
    return {
      isValid: false,
      error:
        "Invalid OLID format. Expected format: OL[numbers][letter] (e.g., OL23919A)",
    };
  }

  return { isValid: true };
}
