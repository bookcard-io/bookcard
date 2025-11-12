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

import { useCallback, useRef, useState } from "react";

export interface UseCoverFromUrlOptions {
  /** Book ID for the cover URL request. */
  bookId: number;
  /** Callback when cover is successfully downloaded. */
  onSuccess?: (tempUrl: string) => void;
}

export interface UseCoverFromUrlResult {
  /** Whether the request is in progress. */
  isLoading: boolean;
  /** Error message if request failed. */
  error: string | null;
  /** Function to download cover from URL. */
  downloadCover: (url: string) => Promise<void>;
  /** Clear the error state. */
  clearError: () => void;
}

/**
 * Custom hook for downloading book cover from URL.
 *
 * Handles API call, loading state, and error handling.
 * Follows SRP by focusing solely on cover-from-url API interaction.
 * Follows IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UseCoverFromUrlOptions
 *     Configuration including book ID and success callback.
 *
 * Returns
 * -------
 * UseCoverFromUrlResult
 *     Loading state, error, and download function.
 */
export function useCoverFromUrl(
  options: UseCoverFromUrlOptions,
): UseCoverFromUrlResult {
  const { bookId, onSuccess } = options;
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Use ref to track loading state to avoid stale closure issues
  const isLoadingRef = useRef(false);

  const downloadCover = useCallback(
    async (url: string) => {
      const trimmedUrl = url.trim();
      if (!trimmedUrl || isLoadingRef.current) {
        return;
      }

      // Set loading state immediately for immediate UI feedback
      isLoadingRef.current = true;
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/books/${bookId}/cover-from-url`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ url: trimmedUrl }),
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "Failed to download cover from URL");
        }

        // Get the full URL for the temp cover
        const tempUrl = data.temp_url;
        const fullTempUrl = tempUrl.startsWith("http")
          ? tempUrl
          : `${window.location.origin}${tempUrl}`;

        onSuccess?.(fullTempUrl);
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Failed to download cover from URL";
        setError(message);
        throw err;
      } finally {
        isLoadingRef.current = false;
        setIsLoading(false);
      }
    },
    [bookId, onSuccess],
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    isLoading,
    error,
    downloadCover,
    clearError,
  };
}
