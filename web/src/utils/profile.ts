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
