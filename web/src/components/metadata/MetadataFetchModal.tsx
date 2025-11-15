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

"use client";

import { useMemo, useRef, useState } from "react";
import { Button } from "@/components/forms/Button";
import { useAutoSearch } from "@/hooks/useAutoSearch";
import { useCollapsibleSection } from "@/hooks/useCollapsibleSection";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import { useMetadataSearchActions } from "@/hooks/useMetadataSearchActions";
import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";
import { useMetadataSearchStream } from "@/hooks/useMetadataSearchStream";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { usePreferredProviders } from "@/hooks/usePreferredProviders";
import { useProviderItems } from "@/hooks/useProviderItems";
import { useProviderSettings } from "@/hooks/useProviderSettings";
import type { Book, BookUpdate } from "@/types/book";
import {
  calculateProvidersForBackend,
  hasFailedProviders,
} from "@/utils/metadata";
import { scrollToProviderResults } from "@/utils/metadataScroll";
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

  // Manage provider settings
  const { enabledProviders } = useProviderSettings();
  const { preferredProviders, togglePreferred } = usePreferredProviders();

  // Calculate providers to send to backend: preferred AND enabled
  const providersForBackend = useMemo(
    () => calculateProvidersForBackend(preferredProviders, enabledProviders),
    [preferredProviders, enabledProviders],
  );

  const searchStream = useMetadataSearchStream({
    query: searchQuery,
    locale,
    maxResultsPerProvider,
    providerIds,
    enableProviders: providersForBackend,
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

  // Check if there are any failed providers for auto-expansion
  const hasFailed = useMemo(
    () => hasFailedProviders(state.providerStatuses),
    [state.providerStatuses],
  );

  // Manage collapsible providers section
  const { isExpanded: isProvidersExpanded, toggle: toggleProvidersExpanded } =
    useCollapsibleSection({
      initialExpanded: true,
      autoExpandOnCondition: true,
      condition: hasFailed,
    });

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
  const providerItems = useProviderItems({
    providerStatuses: state.providerStatuses,
    enabledProviders,
    preferredProviders,
  });

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-1000 modal-overlay-padding-responsive"
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className="modal-container modal-container-shadow-large max-h-[95vh] min-h-[95vh] w-full min-w-[850px] max-w-[60vw] md:max-h-[98vh] md:min-h-[98vh] md:rounded-md"
        role="dialog"
        aria-modal="true"
        aria-label="Fetch metadata"
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={handleClose}
          className="modal-close-button modal-close-button-sm border-0 focus:outline-none"
          aria-label="Close"
        >
          <i className="pi pi-times" aria-hidden="true" />
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
              className="rounded-md border border-danger-a0 bg-[rgba(156,33,33,0.15)] px-3 py-3 text-danger-a10 text-sm"
              role="alert"
            >
              <strong>Error:</strong> {state.error}
            </div>
          )}

          {state.totalProviders > 0 && <MetadataSearchProgress state={state} />}

          <div className="flex flex-col gap-2">
            <button
              type="button"
              className="flex cursor-pointer items-center justify-between gap-2 border-0 bg-transparent p-0 transition-opacity duration-200 hover:opacity-80 focus:rounded focus:outline-none focus:outline-2 focus:outline-primary-a0 focus:outline-offset-2"
              onClick={toggleProvidersExpanded}
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
                    enabled={providerItem.preferred}
                    onToggle={() => togglePreferred(providerItem.name)}
                    onScrollToResults={() =>
                      scrollToProviderResults(providerItem.name)
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
              <div className="rounded-md border border-success-a0 bg-[rgba(34,148,110,0.15)] px-3 py-3 text-center text-sm text-success-a10">
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
