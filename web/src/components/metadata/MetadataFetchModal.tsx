"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
      if (Array.isArray(parsed)) {
        if (parsed.length === 0) {
          // Empty array means user explicitly disabled all providers
          return new Set<string>();
        }
        // If setting has values, only those providers are enabled
        return new Set(parsed);
      }
      // Not an array, default to all enabled
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

  // Get enabled provider names from state
  const enabledProviderNames = useMemo(() => {
    return Array.from(enabledProviders);
  }, [enabledProviders]);

  const searchStream = useMetadataSearchStream({
    query: searchQuery,
    locale,
    maxResultsPerProvider,
    providerIds,
    enableProviders: enabledProviderNames,
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
    // Store the array of enabled provider names
    // Empty array means user explicitly disabled all providers
    // Non-empty array means only those providers are enabled
    // (We don't store a special value for "all enabled" - that's the default when setting doesn't exist)
    const enabledArray = Array.from(next);
    const enabledSet = new Set(enabledArray);
    const allEnabled =
      enabledArray.length === AVAILABLE_METADATA_PROVIDERS.length &&
      AVAILABLE_METADATA_PROVIDERS.every((p) => enabledSet.has(p));

    if (allEnabled) {
      // All providers enabled, delete the setting (default behavior)
      // This distinguishes "all enabled by default" from "user explicitly enabled all"
      // But since we can't delete settings easily, we'll store empty array for now
      // and handle it in the read logic
      // Actually, let's store a special marker or just store all provider names
      // For simplicity, store all provider names when all are enabled
      updateSetting(
        SETTING_KEY,
        JSON.stringify(Array.from(AVAILABLE_METADATA_PROVIDERS)),
      );
    } else {
      // Store the enabled providers array (can be empty if none enabled)
      updateSetting(SETTING_KEY, JSON.stringify(enabledArray));
    }
  };

  // Update expanded state when failed providers appear
  useEffect(() => {
    if (hasFailed && !isProvidersExpanded) {
      setIsProvidersExpanded(true);
    }
  }, [hasFailed, isProvidersExpanded]);

  // Scroll to first result of a provider
  const handleScrollToProviderResults = useCallback((providerName: string) => {
    // First, scroll to the results section container
    const resultsSection = document.getElementById("metadata-results-section");
    if (resultsSection) {
      resultsSection.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }

    // Then, after a short delay, scroll to the specific provider's first result
    // This ensures the results section is visible first
    setTimeout(() => {
      // Normalize provider name to match source_id format
      // e.g., "Google Books" -> "google-books"
      const sourceId = providerName.toLowerCase().replace(/\s+/g, "-");
      const elementId = `result-${sourceId}`;
      const element = document.getElementById(elementId);

      if (element) {
        // Scroll to the element with smooth behavior
        element.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
    }, 100);
  }, []);

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="fixed inset-0 z-[1000] flex animate-[fadeIn_0.2s_ease-out] items-center justify-center overflow-y-auto bg-black/70 p-4 md:p-2"
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className="relative flex max-h-[95vh] min-h-[95vh] w-full min-w-[850px] max-w-[60vw] animate-[slideUp_0.3s_ease-out] flex-col overflow-y-auto rounded-2xl bg-surface-a10 shadow-[0_20px_60px_rgba(0,0,0,0.5)] md:max-h-[98vh] md:min-h-[98vh] md:rounded-xl"
        role="dialog"
        aria-modal="true"
        aria-label="Fetch metadata"
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={handleClose}
          className="absolute top-4 right-4 z-10 flex h-10 w-10 items-center justify-center rounded-full border-0 bg-transparent p-2 text-3xl text-text-a30 leading-none transition-all duration-200 hover:bg-surface-a20 hover:text-text-a0 focus:outline-none focus:outline-2 focus:outline-primary-a0 focus:outline-offset-2"
          aria-label="Close"
        >
          ×
        </button>

        <div className="flex min-h-0 flex-1 flex-col gap-6 p-6 md:gap-4 md:p-4">
          <div className="flex flex-col gap-2">
            <h2 className="m-0 font-bold text-2xl text-text-a0 md:text-xl">
              Fetch Metadata
            </h2>
            <p className="m-0 text-sm text-text-a30">
              Search external sources for book metadata. Click the cover to load
              metadata to the form.
            </p>
          </div>

          <div className="flex flex-row items-start gap-3">
            <div className="min-w-0 flex-1">
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
            <div
              className="rounded-lg border border-danger-a0 bg-[rgba(156,33,33,0.15)] px-3 py-3 text-danger-a10 text-sm"
              role="alert"
            >
              <strong>Error:</strong> {state.error}
            </div>
          )}

          {state.isSearching && state.totalProviders > 0 && (
            <MetadataSearchProgress state={state} />
          )}

          <div className="flex flex-col gap-2">
            <button
              type="button"
              className="flex cursor-pointer items-center justify-between gap-2 border-0 bg-transparent p-0 transition-opacity duration-200 hover:opacity-80 focus:rounded focus:outline-none focus:outline-2 focus:outline-primary-a0 focus:outline-offset-2"
              onClick={() => setIsProvidersExpanded(!isProvidersExpanded)}
              aria-expanded={isProvidersExpanded}
              aria-controls="providers-list"
            >
              <h3 className="m-0 font-semibold text-[0.9rem] text-text-a0">
                Providers
              </h3>
              <span
                className={`pi flex-shrink-0 text-sm text-text-a30 transition-transform duration-200 ${isProvidersExpanded ? "pi-chevron-up" : "pi-chevron-down"}`}
                aria-hidden="true"
              />
            </button>
            {isProvidersExpanded && (
              <div
                id="providers-list"
                className="scrollbar-custom grid max-h-80 grid-cols-3 gap-1.5 overflow-y-auto pr-1 md:max-h-60 [&>*:last-child:nth-child(3n+1):nth-child(n+4)]:col-span-full"
              >
                {providerItems.map((providerItem) => (
                  <MetadataProviderStatus
                    key={providerItem.name}
                    status={providerItem.status}
                    enabled={providerItem.enabled}
                    onToggle={() => handleProviderToggle(providerItem.name)}
                    onScrollToResults={() =>
                      handleScrollToProviderResults(providerItem.name)
                    }
                  />
                ))}
              </div>
            )}
          </div>

          {state.results?.length > 0 && (
            <div id="metadata-results-section" className="flex flex-col gap-2">
              <h3 className="m-0 font-semibold text-[0.9rem] text-text-a0">
                Results
              </h3>
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
              <div className="rounded-lg border border-success-a0 bg-[rgba(34,148,110,0.15)] px-3 py-3 text-center text-sm text-success-a10">
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
