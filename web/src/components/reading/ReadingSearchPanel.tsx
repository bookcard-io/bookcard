// Copyright (C) 2025 khoa and others
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

import { useEffect, useRef, useState } from "react";
import { TextInput } from "@/components/forms/TextInput";
import { ThemeSettingsPanel } from "./components/ThemeSettingsPanel";
import type { SearchResult } from "./EPUBReader";

export interface ReadingSearchPanelProps {
  /** Whether the panel is open. */
  isOpen: boolean;
  /** Callback when the panel should be closed. */
  onClose: () => void;
  /** Current search query. */
  searchQuery?: string;
  /** Callback when search query changes. */
  onSearchQueryChange?: (query: string) => void;
  /** Search results to display. */
  searchResults?: SearchResult[];
  /** Callback when a search result is clicked to navigate to it. */
  onResultClick?: (cfi: string) => void;
  /** Optional className. */
  className?: string;
}

/**
 * Slide-out search panel for the reading page.
 *
 * Allows users to search for words or phrases in the book.
 * Slides in from the right side with smooth animation.
 *
 * Follows SRP by delegating to specialized components.
 * Follows SOC by separating concerns into components and hooks.
 * Follows IOC by accepting callbacks as props.
 * Follows DRY by reusing shared components.
 *
 * Parameters
 * ----------
 * props : ReadingSearchPanelProps
 *     Component props including open state and callbacks.
 */
/**
 * Highlights the search term in a text excerpt.
 *
 * Parameters
 * ----------
 * text : string
 *     The text to highlight in.
 * searchTerm : string
 *     The search term to highlight.
 *
 * Returns
 * -------
 * React.ReactNode
 *     Text with highlighted search terms.
 */
function highlightSearchTerm(
  text: string,
  searchTerm: string,
): React.ReactNode {
  if (!searchTerm.trim()) {
    return text;
  }

  const regex = new RegExp(
    `(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`,
    "gi",
  );
  const parts = text.split(regex);

  return parts.map((part, index) => {
    const key = `${part}-${index}`;
    if (regex.test(part)) {
      return (
        <strong key={key} className="font-semibold underline">
          {part}
        </strong>
      );
    }
    return <span key={key}>{part}</span>;
  });
}

export function ReadingSearchPanel({
  isOpen,
  onClose,
  searchQuery = "",
  onSearchQueryChange,
  searchResults = [],
  onResultClick,
  className,
}: ReadingSearchPanelProps) {
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [localSearchQuery, setLocalSearchQuery] = useState("");

  // Sync local state with prop when panel opens
  useEffect(() => {
    if (isOpen) {
      setLocalSearchQuery(searchQuery);
    }
  }, [isOpen, searchQuery]);

  // Focus the input when the panel opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      // Small delay to ensure the panel animation has started
      const timeoutId = setTimeout(() => {
        searchInputRef.current?.focus();
      }, 100);
      return () => clearTimeout(timeoutId);
    }
    return undefined;
  }, [isOpen]);

  /**
   * Validates if a search query is valid (non-null, non-blank, non-only-space).
   *
   * Parameters
   * ----------
   * query : string
   *     The search query to validate.
   *
   * Returns
   * -------
   * boolean
   *     True if the query is valid, false otherwise.
   */
  const isValidSearchQuery = (query: string): boolean => {
    return query !== null && query.trim().length > 0;
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      const trimmedQuery = localSearchQuery.trim();
      if (isValidSearchQuery(trimmedQuery) && onSearchQueryChange) {
        onSearchQueryChange(trimmedQuery);
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalSearchQuery(e.target.value);
  };

  const handleClear = () => {
    setLocalSearchQuery("");
    if (onSearchQueryChange) {
      onSearchQueryChange("");
    }
    searchInputRef.current?.focus();
  };

  const handleResultClick = (cfi: string) => {
    if (onResultClick) {
      onResultClick(cfi);
    } else {
      // eslint-disable-next-line no-console
      console.warn("onResultClick handler not provided");
    }
  };

  return (
    <ThemeSettingsPanel
      isOpen={isOpen}
      onClose={onClose}
      className={className}
      title="Search in book"
      ariaLabel="Search in book"
      closeAriaLabel="Close search panel"
    >
      <div className="flex h-full flex-col gap-4">
        {/* Search Input with Clear Button */}
        <div className="relative">
          <TextInput
            ref={searchInputRef}
            id="book-search-input"
            placeholder="Search for a word or a phrase"
            value={localSearchQuery}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
          />
          {localSearchQuery && (
            <button
              type="button"
              onClick={handleClear}
              className="-translate-y-1/2 absolute top-1/2 right-3 flex h-6 w-6 items-center justify-center rounded-full transition-colors hover:bg-surface-a20"
              aria-label="Clear search"
            >
              <i className="pi pi-times text-sm text-text-a40" />
            </button>
          )}
        </div>

        {/* Results Count */}
        {searchQuery && (
          <div className="text-sm text-text-a40">
            {searchResults.length}{" "}
            {searchResults.length === 1 ? "result" : "results"} found
          </div>
        )}

        {/* Search Results List */}
        {searchQuery && searchResults.length > 0 && (
          <div className="flex-1 overflow-y-auto">
            <div className="flex flex-col gap-3">
              {searchResults.map((result) => {
                return (
                  <button
                    key={result.cfi}
                    type="button"
                    onClick={() => handleResultClick(result.cfi)}
                    className="rounded-md border border-transparent p-3 text-left transition-colors hover:border-surface-a30 hover:bg-surface-a20"
                  >
                    {result.page && (
                      <div className="mb-1 text-text-a40 text-xs">
                        Page {result.page}
                      </div>
                    )}
                    <div className="text-sm text-text-a0 leading-relaxed">
                      {highlightSearchTerm(result.excerpt, searchQuery)}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Empty State */}
        {searchQuery && searchResults.length === 0 && (
          <div className="flex flex-1 items-center justify-center text-sm text-text-a40">
            No results found
          </div>
        )}
      </div>
    </ThemeSettingsPanel>
  );
}
