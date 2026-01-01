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

import Link from "next/link";
import { FaPlus } from "react-icons/fa";
import type { SearchSuggestion } from "@/types/search";
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
  // Only hide if there are no suggestions AND no query to search for AND not loading
  if (suggestions.length === 0 && !query && !isLoading) {
    return null;
  }

  return (
    <div className="absolute top-[calc(100%+4px)] right-0 left-0 z-[1000] mt-1 max-h-[400px] min-w-[400px] overflow-y-auto rounded-md border border-surface-a20 bg-surface-tonal-a10 shadow-[0_4px_12px_rgba(0,0,0,0.15)]">
      {isLoading ? (
        <div className="flex w-full cursor-pointer items-center gap-3 border-none bg-transparent px-4 py-2.5 text-left transition-colors duration-150">
          Loading...
        </div>
      ) : (
        suggestions.length > 0 && (
          <>
            <div className="border-surface-a20 border-b px-4 py-3 text-[13px] text-text-a30">
              All books containing "{query}"
            </div>
            {suggestions.map((suggestion) => (
              <SearchSuggestionItem
                key={`${suggestion.type}-${suggestion.id}`}
                suggestion={suggestion}
                query={query}
                onClick={onSuggestionClick}
              />
            ))}
          </>
        )
      )}

      {query && (
        <>
          <div className="border-surface-a20 border-b px-4 py-2 text-[13px] text-text-a30">
            Add new books
          </div>
          <Link
            href={`/tracked-books/add?q=${encodeURIComponent(query)}`}
            className="flex w-full cursor-pointer items-center gap-3 border-none bg-transparent px-4 py-3 text-left text-text-a0 no-underline transition-colors duration-150 hover:bg-surface-tonal-a20"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-a10 text-primary-a0">
              <FaPlus className="text-sm" />
            </div>
            <div className="flex flex-col">
              <span className="font-medium text-sm">Search for "{query}"</span>
              <span className="text-text-a30 text-xs">
                Search metadata providers
              </span>
            </div>
          </Link>
        </>
      )}
    </div>
  );
}
