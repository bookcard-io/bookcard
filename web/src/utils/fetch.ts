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
 * Fetch deduplication utilities.
 *
 * Provides centralized fetch deduplication to prevent duplicate API requests
 * across component instances. Follows DRY by centralizing fetch deduplication logic.
 * Follows SRP by focusing solely on request deduplication.
 */

// Global map to track in-flight fetches by key
const inflightFetches = new Map<string, Promise<unknown>>();

/**
 * Deduplicate fetch requests by key.
 *
 * If a fetch with the same key is already in progress, returns the existing
 * Promise. Otherwise, creates a new fetch and stores it in the cache.
 * Automatically cleans up the cache when the Promise settles.
 *
 * Parameters
 * ----------
 * key : string
 *     Unique key identifying this fetch request (e.g., URL + query params).
 * fetchFn : () => Promise<T>
 *     Function that performs the actual fetch.
 *
 * Returns
 * -------
 * Promise<T>
 *     Promise that resolves with the fetch result. Multiple callers with the
 *     same key will receive the same Promise instance.
 */
export async function deduplicateFetch<T>(
  key: string,
  fetchFn: () => Promise<T>,
): Promise<T> {
  // Check if there's already an in-flight fetch for this key
  const existingPromise = inflightFetches.get(key);
  if (existingPromise) {
    return existingPromise as Promise<T>;
  }

  // Create new fetch promise
  const fetchPromise = fetchFn();
  const promise = (async () => {
    try {
      return await fetchPromise;
    } finally {
      // Clean up when promise settles (success or failure)
      // Wait for promise to fully settle before removing
      await Promise.resolve(fetchPromise).then(
        () => {
          inflightFetches.delete(key);
        },
        () => {
          inflightFetches.delete(key);
        },
      );
    }
  })();

  // Store in cache
  inflightFetches.set(key, promise);

  return promise;
}

/**
 * Generate a cache key for a fetch request.
 *
 * Creates a unique string key from URL and optional options.
 * Useful for creating consistent keys across different fetch calls.
 *
 * Parameters
 * ----------
 * url : string
 *     Request URL.
 * options? : RequestInit
 *     Optional fetch options (method, body, etc.).
 *
 * Returns
 * -------
 * string
 *     Cache key string.
 */
export function generateFetchKey(url: string, options?: RequestInit): string {
  const parts = [url];

  if (options?.method && options.method !== "GET") {
    parts.push(`method:${options.method}`);
  }

  if (options?.body) {
    // For JSON bodies, stringify for consistent keys
    if (typeof options.body === "string") {
      parts.push(`body:${options.body}`);
    } else {
      parts.push(`body:${JSON.stringify(options.body)}`);
    }
  }

  return parts.join("|");
}
