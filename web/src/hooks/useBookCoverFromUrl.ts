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
  /** Callback when cover is saved (for updating local state). */
  onCoverSaved?: () => void | Promise<void>;
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
  const { bookId, onUrlInputVisibilityChange, onCoverSaved } = options;

  const {
    isLoading,
    error,
    downloadCover: downloadCoverFromApi,
    clearError,
  } = useCoverFromUrl({
    bookId,
    onSuccess: async () => {
      // Cover is saved directly, no need to stage it
      // Refresh book data after cover is saved
      await onCoverSaved?.();
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
