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
import { useClickOutside } from "@/hooks/useClickOutside";
import { useFilterSuggestions } from "@/hooks/useFilterSuggestions";
import { cn } from "@/libs/utils";
import type { SearchSuggestionItem } from "@/types/search";
import { FilterSuggestionsDropdown } from "./FilterSuggestionsDropdown";

export interface FilterInputProps {
  /**
   * Label for the filter input.
   */
  label: string;
  /**
   * Filter type: 'author', 'title', 'genre', 'publisher', 'identifier', 'series', 'format', 'rating', 'language'.
   */
  filterType: string;
  /**
   * Placeholder text for the input.
   */
  placeholder?: string;
  /**
   * Current filter value (selected suggestion IDs).
   */
  value?: number[];
  /**
   * Selected suggestions (for display).
   */
  selectedSuggestions?: SearchSuggestionItem[];
  /**
   * Callback fired when selected values change.
   */
  onChange?: (ids: number[]) => void;
  /**
   * Callback fired when a suggestion is clicked.
   */
  onSuggestionClick?: (suggestion: SearchSuggestionItem) => void;
}

/**
 * Filter input component with integrated autocomplete suggestions.
 *
 * Provides a text input field for filtering by a specific type with
 * real-time suggestions displayed in a dropdown.
 *
 * Follows SRP by delegating business logic to custom hooks and services.
 * Follows SOC by separating UI, state management, and API concerns.
 * Follows IOC by using dependency injection for the filter service.
 */
export function FilterInput({
  label,
  filterType,
  placeholder = "Type to search",
  value = [],
  selectedSuggestions = [],
  onChange,
  onSuggestionClick,
}: FilterInputProps) {
  const [query, setQuery] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isInputFocused, setIsInputFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Fetch filter suggestions using custom hook
  const { suggestions, isLoading } = useFilterSuggestions({
    query,
    filterType,
    enabled: query.trim().length > 0,
  });

  // Show suggestions when they arrive or when query changes (only if input is focused)
  useEffect(() => {
    if (
      isInputFocused &&
      query.trim().length > 0 &&
      (suggestions.length > 0 || isLoading)
    ) {
      setShowSuggestions(true);
    } else if (query.trim().length === 0) {
      setShowSuggestions(false);
    }
  }, [query, suggestions.length, isLoading, isInputFocused]);

  // Handle click outside to close suggestions
  const containerRef = useClickOutside<HTMLDivElement>(() => {
    setShowSuggestions(false);
  }, showSuggestions);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setQuery(newValue);
  };

  const handleSuggestionClick = (suggestion: SearchSuggestionItem) => {
    // Add suggestion ID to selected values if not already present
    if (!value.includes(suggestion.id)) {
      const newValue = [...value, suggestion.id];
      onChange?.(newValue);
    }
    setQuery("");
    setShowSuggestions(false);
    setIsInputFocused(false);
    onSuggestionClick?.(suggestion);
  };

  const handleFocus = () => {
    setIsInputFocused(true);
    if (inputRef.current && query.trim().length > 0) {
      inputRef.current.select();
      setShowSuggestions(true);
    } else if (query.trim().length > 0) {
      setShowSuggestions(true);
    }
  };

  const handleBlur = () => {
    // Delay to allow click events on suggestions to fire before removing focus
    setTimeout(() => {
      setIsInputFocused(false);
    }, 200);
  };

  const handleRemoveValue = (id: number) => {
    const newValue = value.filter((v) => v !== id);
    onChange?.(newValue);
  };

  const shouldShowDropdown =
    showSuggestions && (suggestions.length > 0 || isLoading);

  // Generate a unique ID for the input to associate with the label
  const inputId = `filter-input-${filterType}-${label.toLowerCase().replace(/\s+/g, "-")}`;

  return (
    <div className="relative flex flex-col gap-2" ref={containerRef}>
      <label htmlFor={inputId} className="font-medium text-[13px] text-text-a0">
        {label}
      </label>
      <div className="relative flex flex-col gap-2">
        <input
          id={inputId}
          ref={inputRef}
          type="text"
          className={cn(
            // Layout
            "w-full",
            // Shape & spacing
            "rounded-lg border border-surface-a30 px-4 py-2.5",
            // Colors
            "bg-surface-tonal-a10 text-text-a0",
            // Typography
            "font-inherit text-sm",
            // Placeholder
            "placeholder:text-text-a40",
            // Transitions
            "transition-[border-color,background-color] duration-200",
            // Hover
            "hover:border-primary-a40",
            // Focus
            "focus:border-primary-a0 focus:bg-surface-tonal-a0 focus:outline-none",
          )}
          placeholder={placeholder}
          value={query}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          aria-label={`Filter by ${label}`}
        />
        {value.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {value.map((id) => {
              // Find the suggestion name for this ID
              const suggestion =
                selectedSuggestions.find((s) => s.id === id) ||
                suggestions.find((s) => s.id === id);
              const displayName = suggestion?.name || `ID: ${id}`;
              return (
                <span
                  key={id}
                  className="inline-flex items-center gap-1.5 rounded-md bg-primary-a0 px-2 py-1 text-text-a0 text-xs"
                >
                  {displayName}
                  <button
                    type="button"
                    className="flex h-4 w-4 items-center justify-center rounded-full border-none bg-transparent p-0 text-text-a0 text-xs leading-none transition-colors duration-150 hover:bg-black/10"
                    onClick={() => handleRemoveValue(id)}
                    aria-label={`Remove ${displayName}`}
                  >
                    <i className="pi pi-times" aria-hidden="true" />
                  </button>
                </span>
              );
            })}
          </div>
        )}
      </div>
      {shouldShowDropdown && (
        <FilterSuggestionsDropdown
          suggestions={suggestions}
          isLoading={isLoading}
          onSuggestionClick={handleSuggestionClick}
        />
      )}
    </div>
  );
}
