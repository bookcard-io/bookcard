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
