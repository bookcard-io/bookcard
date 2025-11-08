import type { SearchSuggestion } from "@/types/search";
import { highlightText } from "@/utils/textHighlight";
import styles from "./SearchInput.module.scss";

export interface SearchSuggestionItemProps {
  /**
   * The search suggestion to display.
   */
  suggestion: SearchSuggestion;
  /**
   * The current search query for highlighting.
   */
  query: string;
  /**
   * Callback fired when the suggestion is clicked.
   */
  onClick: (suggestion: SearchSuggestion) => void;
}

/**
 * Individual search suggestion item component.
 *
 * Displays a suggestion with a type pill and highlighted matching text.
 * Follows SRP by handling only the rendering of a single suggestion.
 */
export function SearchSuggestionItem({
  suggestion,
  query,
  onClick,
}: SearchSuggestionItemProps) {
  const handleClick = () => {
    onClick(suggestion);
  };

  return (
    <button
      type="button"
      className={styles.suggestionItem}
      onClick={handleClick}
    >
      <span className={styles.suggestionPill}>{suggestion.type}</span>
      <span className={styles.suggestionText}>
        {highlightText(suggestion.name, query, styles.highlight as string)}
      </span>
    </button>
  );
}
