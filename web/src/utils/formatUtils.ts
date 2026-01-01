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
 * Supported comic book formats.
 *
 * Single source of truth for comic format detection.
 * Follows OCP by allowing easy extension without modifying detection logic.
 */
export const COMIC_FORMATS = ["CBZ", "CBR", "CB7", "CBC"] as const;

/**
 * Supported audiobook formats.
 *
 * Single source of truth for audiobook format detection.
 */
export const AUDIOBOOK_FORMATS = ["MP3", "M4B", "M4A", "WAV", "FLAC"] as const;

/**
 * All supported readable formats in priority order.
 *
 * EPUB is preferred, then PDF, then comics.
 */
export const READABLE_FORMATS = ["EPUB", "PDF", ...COMIC_FORMATS] as const;

/**
 * Check if a format is a comic book format.
 *
 * Follows OCP by extracting format detection logic from components.
 * Follows DRY by centralizing format detection.
 *
 * Parameters
 * ----------
 * format : string | undefined
 *     File format string (e.g., 'CBZ', 'CBR', 'EPUB').
 *
 * Returns
 * -------
 * boolean
 *     True if format is a comic book format.
 *
 * Example
 * -------
 * ```ts
 * isComicFormat("CBZ")  // true
 * isComicFormat("EPUB")  // false
 * isComicFormat(undefined)  // false
 * ```
 */
export function isComicFormat(format?: string): boolean {
  if (!format) {
    return false;
  }
  const formatUpper = format.toUpperCase();
  return (COMIC_FORMATS as readonly string[]).includes(formatUpper);
}
