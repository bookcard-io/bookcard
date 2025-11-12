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

import type { SearchSuggestionItem } from "@/types/search";

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
      <div className="absolute top-[calc(100%+4px)] right-0 left-0 z-[1000] mt-1 max-h-[300px] overflow-y-auto rounded-lg border border-surface-a20 bg-surface-tonal-a10 shadow-[0_4px_12px_rgba(0,0,0,0.15)]">
        <div className="flex w-full cursor-pointer items-center border-none bg-transparent px-4 py-2.5 text-left text-sm text-text-a0 transition-colors duration-150 first:border-t-0 hover:bg-surface-tonal-a20 focus:bg-surface-tonal-a20 focus:outline-none">
          Loading...
        </div>
      </div>
    );
  }

  if (suggestions.length === 0) {
    return null;
  }

  return (
    <div className="absolute top-[calc(100%+4px)] right-0 left-0 z-[1000] mt-1 max-h-[300px] overflow-y-auto rounded-lg border border-surface-a20 bg-surface-tonal-a10 shadow-[0_4px_12px_rgba(0,0,0,0.15)]">
      {suggestions.map((suggestion) => (
        <button
          key={suggestion.id}
          type="button"
          className="flex w-full cursor-pointer items-center border-none bg-transparent px-4 py-2.5 text-left text-sm text-text-a0 transition-colors duration-150 first:border-t-0 hover:bg-surface-tonal-a20 focus:bg-surface-tonal-a20 focus:outline-none"
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
