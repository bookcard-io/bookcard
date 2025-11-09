"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/forms/Button";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import { useMetadataSearchStream } from "@/hooks/useMetadataSearchStream";
import { useModal } from "@/hooks/useModal";
import type { Book } from "@/types/book";
import { getInitialSearchQuery } from "./getInitialSearchQuery";
import styles from "./MetadataFetchModal.module.scss";
import { MetadataProviderStatus } from "./MetadataProviderStatus";
import { MetadataResultsList } from "./MetadataResultsList";
import { MetadataSearchInput } from "./MetadataSearchInput";
import { MetadataSearchProgress } from "./MetadataSearchProgress";

export interface MetadataFetchModalProps {
  /** Book data to pre-populate search query. */
  book: Book | null;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Locale code for search (default: 'en'). */
  locale?: string;
  /** Maximum results per provider (default: 20). */
  maxResultsPerProvider?: number;
  /** Provider IDs to search (default: all enabled). */
  providerIds?: string[];
}

/**
 * Modal component for fetching book metadata from external sources.
 *
 * Displays search interface with live progress updates via SSE.
 * Follows SRP by delegating to specialized components.
 * Uses IOC via hooks and component composition.
 */
export function MetadataFetchModal({
  book,
  onClose,
  locale = "en",
  maxResultsPerProvider = 20,
  providerIds,
}: MetadataFetchModalProps) {
  const initialQuery = useMemo(() => getInitialSearchQuery(book), [book]);
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const hasAutoSearchedRef = useRef(false);
  const startSearchRef = useRef<((overrideQuery?: string) => void) | null>(
    null,
  );

  const { state, startSearch, cancelSearch, reset } = useMetadataSearchStream({
    query: searchQuery,
    locale,
    maxResultsPerProvider,
    providerIds,
    enabled: false, // Manual trigger
  });

  // Keep ref in sync with latest startSearch function
  useEffect(() => {
    startSearchRef.current = startSearch;
  }, [startSearch]);

  // Check if there are any failed providers to determine default expanded state
  const hasFailedProviders = useMemo(() => {
    return Array.from(state.providerStatuses.values()).some(
      (status) => status.status === "failed",
    );
  }, [state.providerStatuses]);

  const [isProvidersExpanded, setIsProvidersExpanded] = useState(true);

  // Auto-start search when modal opens with initial query (only once)
  useEffect(() => {
    if (hasAutoSearchedRef.current || !initialQuery?.trim()) {
      return;
    }
    setSearchQuery(initialQuery);
    // Small delay to ensure modal is rendered and startSearch is available
    const timer = setTimeout(() => {
      // Double-check flag in case effect ran multiple times
      if (hasAutoSearchedRef.current) {
        return;
      }
      if (startSearchRef.current) {
        hasAutoSearchedRef.current = true; // Set before calling to prevent race conditions
        startSearchRef.current();
      }
    }, 100);
    return () => clearTimeout(timer);
    // startSearch is intentionally omitted - we use startSearchRef which is kept in sync
    // via a separate effect to avoid re-running this effect when startSearch changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery]);

  // Handle keyboard navigation
  useKeyboardNavigation({
    onEscape: onClose,
    enabled: true,
  });

  // Prevent body scroll when modal is open
  useModal(true);

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose],
  );

  const handleModalClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      e.stopPropagation();
    },
    [],
  );

  const handleOverlayKeyDown = useCallback(() => {
    // Keyboard navigation is handled by useKeyboardNavigation hook
  }, []);

  const handleSearch = useCallback(
    (query: string) => {
      const trimmedQuery = query.trim();
      if (trimmedQuery) {
        setSearchQuery(trimmedQuery);
        reset();
        // Start search with the new query immediately
        startSearch(trimmedQuery);
      }
    },
    [reset, startSearch],
  );

  const handleCancel = useCallback(() => {
    cancelSearch();
  }, [cancelSearch]);

  const handleClose = useCallback(() => {
    cancelSearch();
    onClose();
  }, [cancelSearch, onClose]);

  // Convert provider statuses map to array for rendering
  const providerStatusesArray = useMemo(() => {
    return Array.from(state.providerStatuses.values()).sort((a, b) => {
      // Sort by status priority: searching > pending > completed > failed
      const statusOrder: Record<string, number> = {
        searching: 0,
        pending: 1,
        completed: 2,
        failed: 3,
      };
      return (statusOrder[a.status] ?? 99) - (statusOrder[b.status] ?? 99);
    });
  }, [state.providerStatuses]);

  // Update expanded state when failed providers appear
  useEffect(() => {
    if (hasFailedProviders && !isProvidersExpanded) {
      setIsProvidersExpanded(true);
    }
  }, [hasFailedProviders, isProvidersExpanded]);

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className={styles.modalOverlay}
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-label="Fetch metadata"
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={handleClose}
          className={styles.closeButton}
          aria-label="Close"
        >
          ×
        </button>

        <div className={styles.content}>
          <div className={styles.header}>
            <h2 className={styles.title}>Fetch Metadata</h2>
            <p className={styles.subtitle}>
              Search external sources for book metadata. Click the cover to load
              metadata to the form.
            </p>
          </div>

          <div className={styles.searchSection}>
            <div className={styles.searchInputWrapper}>
              <MetadataSearchInput
                ref={searchInputRef}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onSearch={handleSearch}
                isSearching={state.isSearching}
                disabled={false}
              />
            </div>
            {state.isSearching ? (
              <Button
                type="button"
                variant="danger"
                size="medium"
                onClick={handleCancel}
              >
                Cancel Search
              </Button>
            ) : (
              <Button
                type="button"
                variant="primary"
                size="medium"
                onClick={() => handleSearch(searchQuery)}
                disabled={!searchQuery.trim()}
              >
                Search
              </Button>
            )}
          </div>

          {state.error && (
            <div className={styles.error} role="alert">
              <strong>Error:</strong> {state.error}
            </div>
          )}

          {state.isSearching && state.totalProviders > 0 && (
            <MetadataSearchProgress state={state} />
          )}

          {providerStatusesArray.length > 0 && (
            <div className={styles.providersSection}>
              <button
                type="button"
                className={styles.providersHeader}
                onClick={() => setIsProvidersExpanded(!isProvidersExpanded)}
                aria-expanded={isProvidersExpanded}
                aria-controls="providers-list"
              >
                <h3 className={styles.providersTitle}>Providers</h3>
                <span
                  className={`pi ${isProvidersExpanded ? "pi-chevron-up" : "pi-chevron-down"} ${styles.chevronIcon}`}
                  aria-hidden="true"
                />
              </button>
              {isProvidersExpanded && (
                <div id="providers-list" className={styles.providersList}>
                  {providerStatusesArray.map((providerStatus) => (
                    <MetadataProviderStatus
                      key={providerStatus.id}
                      status={providerStatus}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {state.results && state.results.length > 0 && (
            <div className={styles.resultsSection}>
              <h3 className={styles.resultsTitle}>Results</h3>
              <MetadataResultsList results={state.results} />
            </div>
          )}

          {!state.isSearching &&
            state.totalProviders > 0 &&
            state.providersCompleted + state.providersFailed ===
              state.totalProviders && (
              <div className={styles.completedMessage}>
                Search completed. Found {state.totalResults} result
                {state.totalResults !== 1 ? "s" : ""} from{" "}
                {state.providersCompleted} provider
                {state.providersCompleted !== 1 ? "s" : ""}.
              </div>
            )}
        </div>
      </div>
    </div>
  );
}
