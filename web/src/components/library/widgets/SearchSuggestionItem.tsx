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
      className="flex w-full cursor-pointer items-center gap-3 border-none bg-transparent px-4 py-2.5 text-left transition-colors duration-150 first:border-t-0 hover:bg-surface-tonal-a20 focus:bg-surface-tonal-a20 focus:outline-none"
      onClick={handleClick}
    >
      <span className="inline-block min-w-[60px] shrink-0 rounded-full bg-surface-tonal-a50 px-2 py-1 text-center font-medium text-[11px] text-surface-a0 uppercase tracking-[0.5px]">
        {suggestion.type}
      </span>
      <span className="flex-1 text-sm text-text-a0 leading-[1.4]">
        {highlightText(
          suggestion.name,
          query,
          "bg-[#9b59b6] text-text-a0 px-0.5 rounded-sm font-medium",
        )}
      </span>
    </button>
  );
}
