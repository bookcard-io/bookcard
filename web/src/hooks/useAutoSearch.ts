import { useEffect, useRef } from "react";

export interface UseAutoSearchOptions {
  /** Initial query to auto-search with. */
  initialQuery: string | null | undefined;
  /** Function to start the search. */
  startSearch: (overrideQuery?: string) => void;
  /** Callback to update search query state. */
  setSearchQuery?: (query: string) => void;
  /** Whether auto-search is enabled. */
  enabled?: boolean;
}

/**
 * Custom hook for auto-starting search with initial query.
 *
 * Automatically triggers a search when an initial query is provided.
 * Prevents duplicate searches using a ref guard.
 * Follows SRP by focusing solely on auto-search timing logic.
 * Uses IOC via callback dependencies.
 *
 * Parameters
 * ----------
 * options : UseAutoSearchOptions
 *     Options for auto-search behavior.
 */
export function useAutoSearch(options: UseAutoSearchOptions): void {
  const { initialQuery, startSearch, setSearchQuery, enabled = true } = options;
  const hasAutoSearchedRef = useRef(false);
  const startSearchRef = useRef<((overrideQuery?: string) => void) | null>(
    null,
  );
  const setSearchQueryRef = useRef<((query: string) => void) | null>(null);

  // Keep refs in sync with latest functions
  useEffect(() => {
    startSearchRef.current = startSearch;
  }, [startSearch]);

  useEffect(() => {
    setSearchQueryRef.current = setSearchQuery || null;
  }, [setSearchQuery]);

  // Auto-start search when initial query is available (only once)
  useEffect(() => {
    if (!enabled || hasAutoSearchedRef.current || !initialQuery?.trim()) {
      return;
    }

    // Update query state if callback is provided
    if (setSearchQueryRef.current) {
      setSearchQueryRef.current(initialQuery);
    }

    // Small delay to ensure modal is rendered and startSearch is available
    const timer = setTimeout(() => {
      // Double-check flag in case effect ran multiple times
      if (hasAutoSearchedRef.current) {
        return;
      }
      if (startSearchRef.current) {
        hasAutoSearchedRef.current = true; // Set before calling to prevent race conditions
        startSearchRef.current(initialQuery);
      }
    }, 100);

    return () => clearTimeout(timer);
    // startSearch and setSearchQuery are intentionally omitted - we use refs which are kept in sync
    // via separate effects to avoid re-running this effect when they change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery, enabled]);
}
