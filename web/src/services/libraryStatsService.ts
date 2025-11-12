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
 * Library stats service.
 *
 * Provides functions for fetching library statistics from the API.
 * Follows IOC pattern by being a pure function service.
 * Follows DRY by centralizing API call logic.
 */

export interface LibraryStats {
  total_books: number;
  total_series: number;
  total_authors: number;
  total_tags: number;
  total_ratings: number;
  total_content_size: number;
}

/**
 * Fetch library statistics from the API.
 *
 * Parameters
 * ----------
 * libraryId : number
 *     Library identifier.
 *
 * Returns
 * -------
 * Promise<LibraryStats | null>
 *     Library statistics if successful, null otherwise.
 */
export async function fetchLibraryStats(
  libraryId: number,
): Promise<LibraryStats | null> {
  try {
    const response = await fetch(`/api/admin/libraries/${libraryId}/stats`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    const data = (await response.json()) as LibraryStats;
    return data;
  } catch {
    return null;
  }
}
