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

import type { SearchSuggestion } from "@/types/search";
import styles from "./SearchInput.module.scss";
import { SearchSuggestionItem } from "./SearchSuggestionItem";

export interface SearchSuggestionsDropdownProps {
  /**
   * List of search suggestions to display.
   */
  suggestions: SearchSuggestion[];
  /**
   * The current search query.
   */
  query: string;
  /**
   * Whether suggestions are currently being loaded.
   */
  isLoading: boolean;
  /**
   * Callback fired when a suggestion is clicked.
   */
  onSuggestionClick: (suggestion: SearchSuggestion) => void;
}

/**
 * Search suggestions dropdown component.
 *
 * Displays a list of search suggestions in a dropdown menu.
 * Follows SRP by handling only the rendering of the suggestions list.
 */
export function SearchSuggestionsDropdown({
  suggestions,
  query,
  isLoading,
  onSuggestionClick,
}: SearchSuggestionsDropdownProps) {
  if (isLoading) {
    return (
      <div className={styles.suggestionsDropdown}>
        <div className={styles.suggestionItem}>Loading...</div>
      </div>
    );
  }

  if (suggestions.length === 0) {
    return null;
  }

  return (
    <div className={styles.suggestionsDropdown}>
      <div className={styles.suggestionsHeader}>
        All books containing {query}
      </div>
      {suggestions.map((suggestion) => (
        <SearchSuggestionItem
          key={`${suggestion.type}-${suggestion.id}`}
          suggestion={suggestion}
          query={query}
          onClick={onSuggestionClick}
        />
      ))}
    </div>
  );
}
