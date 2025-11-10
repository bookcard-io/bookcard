import { useCallback, useEffect, useState } from "react";

export interface UseStagedCoverUrlOptions {
  /** Book ID to reset staged cover when it changes. */
  bookId: number | null;
  /** Callback when staged cover is set. */
  onCoverSet?: (url: string | null) => void;
}

export interface UseStagedCoverUrlResult {
  /** Currently staged cover URL. */
  stagedCoverUrl: string | null;
  /** Function to set the staged cover URL. */
  setStagedCoverUrl: (url: string | null) => void;
  /** Function to clear the staged cover URL. */
  clearStagedCoverUrl: () => void;
}

/**
 * Custom hook for managing staged cover URL state.
 *
 * Handles resetting when book changes and provides clear interface.
 * Follows SRP by focusing solely on staged cover state management.
 * Follows IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UseStagedCoverUrlOptions
 *     Configuration including book ID and callback.
 *
 * Returns
 * -------
 * UseStagedCoverUrlResult
 *     Staged cover state and control functions.
 */
export function useStagedCoverUrl(
  options: UseStagedCoverUrlOptions,
): UseStagedCoverUrlResult {
  const { bookId, onCoverSet } = options;
  const [stagedCoverUrl, setStagedCoverUrlState] = useState<string | null>(
    null,
  );

  // Reset staged cover URL when bookId changes
  useEffect(() => {
    if (bookId !== null) {
      setStagedCoverUrlState(null);
    }
  }, [bookId]);

  const setStagedCoverUrl = useCallback(
    (url: string | null) => {
      setStagedCoverUrlState(url);
      onCoverSet?.(url);
    },
    [onCoverSet],
  );

  const clearStagedCoverUrl = useCallback(() => {
    setStagedCoverUrlState(null);
    onCoverSet?.(null);
  }, [onCoverSet]);

  return {
    stagedCoverUrl,
    setStagedCoverUrl,
    clearStagedCoverUrl,
  };
}
