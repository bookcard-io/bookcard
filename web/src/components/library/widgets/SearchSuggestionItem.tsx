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
