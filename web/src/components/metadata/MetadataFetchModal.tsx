"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/forms/Button";
import { AVAILABLE_METADATA_PROVIDERS } from "@/components/profile/config/configurationConstants";
import { useUser } from "@/contexts/UserContext";
import { useAutoSearch } from "@/hooks/useAutoSearch";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import { useMetadataSearchActions } from "@/hooks/useMetadataSearchActions";
import type {
  MetadataRecord,
  ProviderStatus,
} from "@/hooks/useMetadataSearchStream";
import { useMetadataSearchStream } from "@/hooks/useMetadataSearchStream";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import type { Book, BookUpdate } from "@/types/book";
import { hasFailedProviders } from "@/utils/metadata";
import { getInitialSearchQuery } from "./getInitialSearchQuery";
import styles from "./MetadataFetchModal.module.scss";
import { MetadataProviderStatus } from "./MetadataProviderStatus";
import { MetadataResultsList } from "./MetadataResultsList";
import { MetadataSearchInput } from "./MetadataSearchInput";
import { MetadataSearchProgress } from "./MetadataSearchProgress";

export interface MetadataFetchModalProps {
  /** Book data to pre-populate search query. */
  book: Book | null;
  /** Optional form data that takes priority over book data for initial query. */
  formData?: BookUpdate | null;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when a metadata record is selected. */
  onSelectMetadata?: (record: MetadataRecord) => void;
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
  formData,
  onClose,
  onSelectMetadata,
  locale = "en",
  maxResultsPerProvider = 20,
  providerIds,
}: MetadataFetchModalProps) {
  const initialQuery = useMemo(
    () => getInitialSearchQuery(book, formData),
    [book, formData],
  );
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const searchStream = useMetadataSearchStream({
    query: searchQuery,
    locale,
    maxResultsPerProvider,
    providerIds,
    enabled: false, // Manual trigger
  });

  const { state, startSearch } = searchStream;

  // Auto-start search when modal opens with initial query
  useAutoSearch({
    initialQuery,
    startSearch,
    setSearchQuery,
    enabled: true,
  });

  // Check if there are any failed providers to determine default expanded state
  const hasFailed = useMemo(
    () => hasFailedProviders(state.providerStatuses),
    [state.providerStatuses],
  );

  const [isProvidersExpanded, setIsProvidersExpanded] = useState(true);

  // Access user context for settings
  const { getSetting, updateSetting, isLoading: isSettingsLoading } = useUser();

  // Load enabled providers from backend setting
  const SETTING_KEY = "preferred_metadata_providers";
  const enabledProvidersFromSetting = useMemo(() => {
    if (isSettingsLoading) {
      return new Set<string>();
    }
    const settingValue = getSetting(SETTING_KEY);
    if (!settingValue) {
      // If no setting, all providers are enabled by default
      return new Set(AVAILABLE_METADATA_PROVIDERS);
    }
    try {
      const parsed = JSON.parse(settingValue) as string[];
      if (Array.isArray(parsed) && parsed.length > 0) {
        // If setting has values, only those providers are enabled
        return new Set(parsed);
      }
      // Empty array means all providers enabled
      return new Set(AVAILABLE_METADATA_PROVIDERS);
    } catch {
      // Invalid JSON, default to all enabled
      return new Set(AVAILABLE_METADATA_PROVIDERS);
    }
  }, [getSetting, isSettingsLoading]);

  // Track enabled providers state
  const [enabledProviders, setEnabledProviders] = useState<Set<string>>(
    enabledProvidersFromSetting,
  );

  // Sync with setting when it loads or changes
  useEffect(() => {
    if (!isSettingsLoading) {
      setEnabledProviders(enabledProvidersFromSetting);
    }
  }, [enabledProvidersFromSetting, isSettingsLoading]);

  // Handle keyboard navigation
  useKeyboardNavigation({
    onEscape: onClose,
    enabled: true,
  });

  // Prevent body scroll when modal is open
  useModal(true);

  // Modal interaction handlers
  const { handleOverlayClick, handleModalClick, handleOverlayKeyDown } =
    useModalInteractions({ onClose });

  // Search action handlers
  const { handleSearch, handleCancel, handleClose } = useMetadataSearchActions({
    searchStream,
    setSearchQuery,
    onClose,
  });

  // Create provider items with status from backend, matching by name
  const providerItems = useMemo(() => {
    return AVAILABLE_METADATA_PROVIDERS.map((providerName) => {
      // Find matching status by name
      let status: ProviderStatus | undefined;
      for (const providerStatus of state.providerStatuses.values()) {
        if (providerStatus.name === providerName) {
          status = providerStatus;
          break;
        }
      }

      // If no status found, create a default pending status
      if (!status) {
        status = {
          id: providerName.toLowerCase().replace(/\s+/g, "-"),
          name: providerName,
          status: "pending",
          resultCount: 0,
          discovered: 0,
        };
      }

      return {
        name: providerName,
        status,
        enabled: enabledProviders.has(providerName),
      };
    });
  }, [state.providerStatuses, enabledProviders]);

  // Handle provider enable/disable toggle
  const handleProviderToggle = (providerName: string) => {
    // Calculate new state first
    const next = new Set(enabledProviders);
    if (next.has(providerName)) {
      next.delete(providerName);
    } else {
      next.add(providerName);
    }

    // Update local state
    setEnabledProviders(next);

    // Update backend setting
    // If all providers are enabled, store empty array (means all enabled)
    // Otherwise, store the array of enabled provider names
    const enabledArray = Array.from(next);
    const enabledSet = new Set(enabledArray);
    const allEnabled =
      enabledArray.length === AVAILABLE_METADATA_PROVIDERS.length &&
      AVAILABLE_METADATA_PROVIDERS.every((p) => enabledSet.has(p));

    if (allEnabled) {
      // All providers enabled, store empty array
      updateSetting(SETTING_KEY, JSON.stringify([]));
    } else {
      // Store the enabled providers array
      updateSetting(SETTING_KEY, JSON.stringify(enabledArray));
    }
  };

  // Update expanded state when failed providers appear
  useEffect(() => {
    if (hasFailed && !isProvidersExpanded) {
      setIsProvidersExpanded(true);
    }
  }, [hasFailed, isProvidersExpanded]);

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
                {providerItems.map((providerItem) => (
                  <MetadataProviderStatus
                    key={providerItem.name}
                    status={providerItem.status}
                    enabled={providerItem.enabled}
                    onToggle={() => handleProviderToggle(providerItem.name)}
                  />
                ))}
              </div>
            )}
          </div>

          {state.results?.length > 0 && (
            <div className={styles.resultsSection}>
              <h3 className={styles.resultsTitle}>Results</h3>
              <MetadataResultsList
                results={state.results}
                onSelectMetadata={onSelectMetadata}
              />
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
