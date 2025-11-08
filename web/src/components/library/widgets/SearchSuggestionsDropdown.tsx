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
