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

import type React from "react";
import { useEffect, useRef, useState } from "react";
import { useSearchSuggestions } from "@/hooks/useSearchSuggestions";
import { Search } from "@/icons/Search";
import type { SearchSuggestionsService } from "@/services/searchSuggestionsService";
import type { SearchSuggestion } from "@/types/search";
import { SearchSuggestionsDropdown } from "./SearchSuggestionsDropdown";

export interface SearchInputProps {
  /**
   * Placeholder text for the search input.
   */
  placeholder?: string;
  /**
   * Current search value.
   */
  value?: string;
  /**
   * Callback fired when the search value changes.
   */
  onChange?: (value: string) => void;
  /**
   * Callback fired when the search input is submitted.
   */
  onSubmit?: (value: string) => void;
  /**
   * Callback fired when a suggestion is clicked.
   * Receives the suggestion object to allow type-specific handling.
   */
  onSuggestionClick?: (suggestion: SearchSuggestion) => void;
  /**
   * Service to fetch search suggestions.
   * If not provided, uses the default service.
   */
  suggestionsService?: SearchSuggestionsService;
}

/**
 * Search input component with integrated search icon and autocomplete suggestions.
 *
 * Provides a text input field for searching books, tags, and authors with
 * real-time search suggestions displayed in a dropdown.
 *
 * Follows SRP by delegating business logic to custom hooks and services.
 * Follows SOC by separating UI, state management, and API concerns.
 * Follows IOC by using dependency injection for the search service.
 */
export function SearchInput({
  placeholder = "Search books, series, tags, and authors",
  value = "",
  onChange,
  onSubmit,
  onSuggestionClick,
  suggestionsService,
}: SearchInputProps) {
  const [query, setQuery] = useState(value);
  const [isInputFocused, setIsInputFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Update local query when value prop changes
  useEffect(() => {
    setQuery(value);
  }, [value]);

  // Fetch search suggestions using custom hook
  const { suggestions, isLoading } = useSearchSuggestions({
    query,
    enabled: query.trim().length > 0,
    service: suggestionsService,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setQuery(newValue);
    onChange?.(newValue);
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    inputRef.current?.blur();
    onSubmit?.(query);
  };

  const handleSuggestionClick = (suggestion: SearchSuggestion) => {
    setQuery(suggestion.name);
    onChange?.(suggestion.name);
    setIsInputFocused(false); // Remove focus to prevent dropdown from reopening

    // If custom handler provided, use it; otherwise fall back to default behavior
    if (onSuggestionClick) {
      onSuggestionClick(suggestion);
    } else {
      // Default: submit search for all types
      onSubmit?.(suggestion.name);
    }
  };

  const handleFocus = () => {
    setIsInputFocused(true);
    // Select all text if there's content when focusing
    if (inputRef.current && query.trim().length > 0) {
      inputRef.current.select();
    }
  };

  const handleBlur = () => {
    // Delay to allow click events on suggestions to fire before removing focus
    setTimeout(() => {
      setIsInputFocused(false);
    }, 200);
  };

  const shouldShowDropdown = isInputFocused && query.trim().length > 0;

  return (
    <div className="relative min-w-0 flex-1">
      <form className="min-w-0 flex-1" onSubmit={handleSubmit}>
        <div className="relative flex w-full items-center">
          <Search
            className="pointer-events-none absolute left-3 z-[1] h-[18px] w-[18px] text-text-a30"
            aria-hidden="true"
          />
          <input
            ref={inputRef}
            type="text"
            className="input-tonal pr-4 pl-10 font-inherit"
            placeholder={placeholder}
            value={query}
            onChange={handleChange}
            onFocus={handleFocus}
            onBlur={handleBlur}
            aria-label="Search books, tags & authors"
          />
        </div>
      </form>
      {shouldShowDropdown && (
        <SearchSuggestionsDropdown
          suggestions={suggestions}
          query={query}
          isLoading={isLoading}
          onSuggestionClick={handleSuggestionClick}
        />
      )}
    </div>
  );
}
