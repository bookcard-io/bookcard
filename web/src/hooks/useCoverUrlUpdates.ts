import { useCallback, useEffect, useState } from "react";
import { getCoverUrlWithCacheBuster } from "@/utils/books";

export interface UseCoverUrlUpdatesOptions {
  /** Ref to expose update method externally. */
  updateRef?: React.RefObject<{
    updateCover: (bookId: number) => void;
  }>;
}

export interface UseCoverUrlUpdatesResult {
  /** Map of book ID to updated cover URL. */
  coverUrlOverrides: Map<number, string>;
  /** Function to update cover URL for a specific book. */
  updateCover: (bookId: number) => void;
  /** Function to clear all cover URL overrides. */
  clearOverrides: () => void;
}

/**
 * Custom hook for managing cover URL updates in book lists.
 *
 * Tracks cover URL overrides by book ID and provides methods to update them.
 * Follows SRP by focusing solely on cover URL override state management.
 * Follows IOC by accepting ref for external access.
 * Follows DRY by centralizing cover URL update logic.
 *
 * Parameters
 * ----------
 * options : UseCoverUrlUpdatesOptions
 *     Configuration including optional ref for external access.
 *
 * Returns
 * -------
 * UseCoverUrlUpdatesResult
 *     Cover URL overrides map and control functions.
 */
export function useCoverUrlUpdates(
  options: UseCoverUrlUpdatesOptions = {},
): UseCoverUrlUpdatesResult {
  const { updateRef } = options;
  const [coverUrlOverrides, setCoverUrlOverrides] = useState<
    Map<number, string>
  >(new Map());

  const updateCover = useCallback((bookId: number) => {
    const newUrl = getCoverUrlWithCacheBuster(bookId);
    setCoverUrlOverrides((prev) => {
      const next = new Map(prev);
      next.set(bookId, newUrl);
      return next;
    });
  }, []);

  const clearOverrides = useCallback(() => {
    setCoverUrlOverrides(new Map());
  }, []);

  // Expose updateCover method via ref
  useEffect(() => {
    if (updateRef) {
      updateRef.current = { updateCover };
    }
  }, [updateRef, updateCover]);

  return {
    coverUrlOverrides,
    updateCover,
    clearOverrides,
  };
}
