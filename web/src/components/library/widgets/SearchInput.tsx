"use client";

import type React from "react";
import { useEffect, useRef, useState } from "react";
import { useClickOutside } from "@/hooks/useClickOutside";
import { useSearchSuggestions } from "@/hooks/useSearchSuggestions";
import { Search } from "@/icons/Search";
import type { SearchSuggestion } from "@/types/search";
import styles from "./SearchInput.module.scss";
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
  placeholder = "Search books, tags & authors",
  value = "",
  onChange,
  onSubmit,
  onSuggestionClick,
}: SearchInputProps) {
  const [query, setQuery] = useState(value);
  const [showSuggestions, setShowSuggestions] = useState(false);
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
    onChange?.(newValue);
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setShowSuggestions(false);
    onSubmit?.(query);
  };

  const handleSuggestionClick = (suggestion: SearchSuggestion) => {
    setQuery(suggestion.name);
    onChange?.(suggestion.name);
    setShowSuggestions(false);
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

  const shouldShowDropdown =
    showSuggestions && (suggestions.length > 0 || isLoading);

  return (
    <div className={styles.searchWrapper} ref={containerRef}>
      <form className={styles.searchForm} onSubmit={handleSubmit}>
        <div className={styles.searchContainer}>
          <Search className={styles.searchIcon} aria-hidden="true" />
          <input
            ref={inputRef}
            type="text"
            className={styles.searchInput}
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
