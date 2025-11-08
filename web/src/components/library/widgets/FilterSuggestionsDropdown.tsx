import type { SearchSuggestionItem } from "@/types/search";
import styles from "./FilterInput.module.scss";

export interface FilterSuggestionsDropdownProps {
  /**
   * List of filter suggestions to display.
   */
  suggestions: SearchSuggestionItem[];
  /**
   * Whether suggestions are currently being loaded.
   */
  isLoading: boolean;
  /**
   * Callback fired when a suggestion is clicked.
   */
  onSuggestionClick: (suggestion: SearchSuggestionItem) => void;
}

/**
 * Filter suggestions dropdown component.
 *
 * Displays a list of filter suggestions in a dropdown menu.
 * Follows SRP by handling only the rendering of the suggestions list.
 */
export function FilterSuggestionsDropdown({
  suggestions,
  isLoading,
  onSuggestionClick,
}: FilterSuggestionsDropdownProps) {
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
      {suggestions.map((suggestion) => (
        <button
          key={suggestion.id}
          type="button"
          className={styles.suggestionItem}
          onMouseDown={(e) => {
            // Prevent input blur from firing before we handle selection
            e.preventDefault();
            onSuggestionClick(suggestion);
          }}
          onClick={() => onSuggestionClick(suggestion)}
        >
          {suggestion.name}
        </button>
      ))}
    </div>
  );
}
