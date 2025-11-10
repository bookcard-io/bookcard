import { useCallback, useRef } from "react";
import { useCoverFromUrl } from "./useCoverFromUrl";
import { useCoverUrlInput } from "./useCoverUrlInput";

export interface UseBookCoverFromUrlOptions {
  /** Book ID for the cover URL request. */
  bookId: number;
  /** Callback when cover is successfully downloaded. */
  onCoverUrlSet?: (url: string) => void;
  /** Callback when URL input visibility changes. */
  onUrlInputVisibilityChange?: (isVisible: boolean) => void;
}

export interface UseBookCoverFromUrlResult {
  /** Whether the cover download is in progress. */
  isLoading: boolean;
  /** Error message if download failed. */
  error: string | null;
  /** URL input state and handlers. */
  urlInput: ReturnType<typeof useCoverUrlInput>;
  /** Handler for URL input change events. */
  handleUrlChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  /** Handler for "Set cover from URL" button click. */
  handleSetFromUrlClick: () => void;
  /** Function to download cover from URL. */
  downloadCover: (url: string) => Promise<void>;
}

/**
 * Custom hook for managing book cover from URL functionality.
 *
 * Encapsulates cover download logic, URL input state, and user interactions.
 * Follows SRP by focusing solely on cover-from-URL business logic.
 * Follows IOC by accepting callbacks as dependencies.
 * Follows DRY by centralizing related logic.
 *
 * Parameters
 * ----------
 * options : UseBookCoverFromUrlOptions
 *     Configuration including book ID and callbacks.
 *
 * Returns
 * -------
 * UseBookCoverFromUrlResult
 *     State, handlers, and functions for cover-from-URL functionality.
 */
export function useBookCoverFromUrl(
  options: UseBookCoverFromUrlOptions,
): UseBookCoverFromUrlResult {
  const { bookId, onCoverUrlSet, onUrlInputVisibilityChange } = options;

  const {
    isLoading,
    error,
    downloadCover: downloadCoverFromApi,
    clearError,
  } = useCoverFromUrl({
    bookId,
    onSuccess: (tempUrl) => {
      onCoverUrlSet?.(tempUrl);
    },
  });

  // Use ref to store hide function to avoid circular dependency
  const hideInputRef = useRef<(() => void) | null>(null);

  const handleUrlSubmit = useCallback(
    async (url: string) => {
      if (!isLoading) {
        try {
          await downloadCoverFromApi(url);
          hideInputRef.current?.();
        } catch {
          // Error is handled by useCoverFromUrl hook
        }
      }
    },
    [isLoading, downloadCoverFromApi],
  );

  const urlInput = useCoverUrlInput({
    onVisibilityChange: onUrlInputVisibilityChange,
    onSubmit: handleUrlSubmit,
  });

  // Store hide function in ref after urlInput is created
  hideInputRef.current = urlInput.hide;

  const handleUrlChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      urlInput.handleChange(e);
      clearError();
    },
    [urlInput, clearError],
  );

  const handleSetFromUrlClick = useCallback(() => {
    if (urlInput.isVisible) {
      const trimmedValue = urlInput.value.trim();
      if (trimmedValue) {
        // Submit if input has a value (hide is handled in handleUrlSubmit)
        handleUrlSubmit(trimmedValue);
      } else {
        // Hide if input is empty
        urlInput.hide();
      }
    } else {
      // Show input if not visible
      urlInput.show();
    }
  }, [urlInput, handleUrlSubmit]);

  return {
    isLoading,
    error,
    urlInput,
    handleUrlChange,
    handleSetFromUrlClick,
    downloadCover: handleUrlSubmit,
  };
}
