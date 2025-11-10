import { useCallback, useState } from "react";

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

  const downloadCover = useCallback(
    async (url: string) => {
      const trimmedUrl = url.trim();
      if (!trimmedUrl || isLoading) {
        return;
      }

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
        setIsLoading(false);
      }
    },
    [bookId, isLoading, onSuccess],
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
