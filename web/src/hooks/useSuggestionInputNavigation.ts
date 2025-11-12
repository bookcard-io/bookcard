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

import { useCallback } from "react";

export interface UseSuggestionInputNavigationOptions<T = string> {
  /** Whether suggestions are currently visible. */
  showSuggestions: boolean;
  /** List of suggestions. */
  suggestions: T[];
  /** Currently selected suggestion index. */
  selectedIndex: number;
  /** Current input value (fallback if no suggestion selected). */
  value: string;
  /** Function to extract value from suggestion item. */
  getSuggestionValue: (suggestion: T) => string;
  /** Callback when a suggestion is selected. */
  onSelectSuggestion: (suggestion: string) => void;
  /** Callback when Enter is pressed without selection. */
  onSubmit: () => void;
  /** Callback to move selection to next item. */
  onSelectNext: () => void;
  /** Callback to move selection to previous item. */
  onSelectPrevious: () => void;
  /** Callback to hide suggestions. */
  onHideSuggestions: () => void;
}

export interface UseSuggestionInputNavigationResult {
  /** Keyboard event handler for the input. */
  handleKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
}

/**
 * Custom hook for handling keyboard navigation in suggestion inputs.
 *
 * Handles Enter, Tab, ArrowDown, and ArrowUp keys for suggestion navigation.
 * Follows SRP by focusing solely on keyboard event handling.
 * Uses IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UseSuggestionInputNavigationOptions
 *     Configuration including callbacks and state.
 *
 * Returns
 * -------
 * UseSuggestionInputNavigationResult
 *     Keyboard event handler.
 */
export function useSuggestionInputNavigation<T = string>(
  options: UseSuggestionInputNavigationOptions<T>,
): UseSuggestionInputNavigationResult {
  const {
    showSuggestions,
    suggestions,
    selectedIndex,
    value,
    getSuggestionValue,
    onSelectSuggestion,
    onSubmit,
    onSelectNext,
    onSelectPrevious,
    onHideSuggestions,
  } = options;

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        if (showSuggestions && suggestions.length > 0 && selectedIndex >= 0) {
          e.preventDefault();
          const selected = suggestions[selectedIndex];
          const chosen = selected ? getSuggestionValue(selected) : value;
          onSelectSuggestion(chosen);
          onHideSuggestions();
        } else {
          onSubmit();
        }
      } else if (e.key === "Tab" && showSuggestions && suggestions.length > 0) {
        e.preventDefault();
        const selected =
          selectedIndex >= 0 ? suggestions[selectedIndex] : suggestions[0];
        const chosen = selected ? getSuggestionValue(selected) : value;
        onSelectSuggestion(chosen);
        onHideSuggestions();
      } else if (
        (e.key === "ArrowDown" || e.key === "Down") &&
        showSuggestions &&
        suggestions.length > 0
      ) {
        e.preventDefault();
        onSelectNext();
      } else if (
        (e.key === "ArrowUp" || e.key === "Up") &&
        showSuggestions &&
        suggestions.length > 0
      ) {
        e.preventDefault();
        onSelectPrevious();
      }
    },
    [
      showSuggestions,
      suggestions,
      selectedIndex,
      value,
      getSuggestionValue,
      onSelectSuggestion,
      onSubmit,
      onSelectNext,
      onSelectPrevious,
      onHideSuggestions,
    ],
  );

  return {
    handleKeyDown,
  };
}
