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

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef } from "react";
import { normalizeAuthorKey } from "@/utils/openLibrary";

export interface UseAuthorPollingOptions {
  /** Maximum number of polling attempts (default: 15). */
  maxAttempts?: number;
  /** Polling interval in milliseconds (default: 2000). */
  pollIntervalMs?: number;
}

export interface UseAuthorPollingResult {
  /** Start polling for an author and navigate when available. */
  pollForAuthor: (openlibraryKey: string) => Promise<void>;
}

/**
 * Custom hook for polling author availability.
 *
 * Polls for author availability after rematch, then navigates to the new
 * author page once found. Follows SRP by managing only polling concerns.
 * Follows IOC by accepting configuration options.
 *
 * Parameters
 * ----------
 * options : UseAuthorPollingOptions
 *     Polling configuration options.
 *
 * Returns
 * -------
 * UseAuthorPollingResult
 *     Function to start polling for an author.
 */
export function useAuthorPolling(
  options: UseAuthorPollingOptions = {},
): UseAuthorPollingResult {
  const { maxAttempts = 15, pollIntervalMs = 2000 } = options;
  const router = useRouter();
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Poll for author availability after rematch.
   *
   * Checks if the author with the given OpenLibrary key is available,
   * then navigates to the new author page once found.
   *
   * Parameters
   * ----------
   * openlibraryKey : string
   *     Normalized OpenLibrary key (e.g., "OL52940A").
   */
  const pollForAuthor = useCallback(
    async (openlibraryKey: string): Promise<void> => {
      // Normalize the key: remove /authors/ prefix if present
      const normalizedKey = normalizeAuthorKey(openlibraryKey);
      let attempts = 0;

      const poll = async (): Promise<void> => {
        attempts += 1;

        try {
          const response = await fetch(`/api/authors/${normalizedKey}`);
          if (response.ok) {
            // Author is available, navigate to the new page
            router.push(`/authors/${normalizedKey}`);
            return;
          }
        } catch (error) {
          // Author not available yet, continue polling
          console.debug(
            `Polling for author ${normalizedKey}, attempt ${attempts}/${maxAttempts}:`,
            error,
          );
        }

        if (attempts < maxAttempts) {
          pollingIntervalRef.current = setTimeout(poll, pollIntervalMs);
        } else {
          // Max attempts reached, navigate anyway (user can refresh if needed)
          console.warn(
            `Max polling attempts reached for author ${normalizedKey}, navigating anyway`,
          );
          router.push(`/authors/${normalizedKey}`);
        }
      };

      // Start polling after initial delay
      pollingIntervalRef.current = setTimeout(poll, pollIntervalMs);
    },
    [router, maxAttempts, pollIntervalMs],
  );

  // Cleanup polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearTimeout(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, []);

  return { pollForAuthor };
}
