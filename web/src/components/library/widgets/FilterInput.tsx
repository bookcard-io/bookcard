"use client";

import type React from "react";
import { useEffect, useRef, useState } from "react";
import { useClickOutside } from "@/hooks/useClickOutside";
import { useFilterSuggestions } from "@/hooks/useFilterSuggestions";
import type { SearchSuggestionItem } from "@/types/search";
import styles from "./FilterInput.module.scss";
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
    <div className={styles.filterInputWrapper} ref={containerRef}>
      <label htmlFor={inputId} className={styles.filterLabel}>
        {label}
      </label>
      <div className={styles.inputContainer}>
        <input
          id={inputId}
          ref={inputRef}
          type="text"
          className={styles.filterInput}
          placeholder={placeholder}
          value={query}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          aria-label={`Filter by ${label}`}
        />
        {value.length > 0 && (
          <div className={styles.selectedValues}>
            {value.map((id) => {
              // Find the suggestion name for this ID
              const suggestion =
                selectedSuggestions.find((s) => s.id === id) ||
                suggestions.find((s) => s.id === id);
              const displayName = suggestion?.name || `ID: ${id}`;
              return (
                <span key={id} className={styles.selectedValue}>
                  {displayName}
                  <button
                    type="button"
                    className={styles.removeButton}
                    onClick={() => handleRemoveValue(id)}
                    aria-label={`Remove ${displayName}`}
                  >
                    ×
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
