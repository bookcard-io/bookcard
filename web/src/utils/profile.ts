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
 * Profile-related utility functions.
 *
 * Provides reusable functions for profile data manipulation.
 * Follows SRP by separating profile manipulation logic from presentation.
 * Follows DRY by centralizing profile-related utilities.
 */

/**
 * Generate cache-busting profile picture URL.
 *
 * Parameters
 * ----------
 * cacheBuster? : number
 *     Optional cache-busting timestamp. Defaults to current time.
 *
 * Returns
 * -------
 * string
 *     Profile picture URL with cache-busting parameter.
 */
export function getProfilePictureUrlWithCacheBuster(
  cacheBuster?: number,
): string {
  const baseUrl = "/api/auth/profile-picture";
  const timestamp = cacheBuster ?? Date.now();
  return `${baseUrl}?v=${timestamp}`;
}
