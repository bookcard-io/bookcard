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

"use client";

import { useCallback, useEffect } from "react";
import { useListSelection } from "@/hooks/useListSelection";
import { useSuggestionInputNavigation } from "@/hooks/useSuggestionInputNavigation";
import { cn } from "@/libs/utils";
import { usePathSuggestions } from "./hooks/usePathSuggestions";

type Props = {
  value: string;
  onChange: (val: string) => void;
  onSubmit: () => void;
  busy?: boolean;
};

/**
 * Path input component with directory suggestions.
 *
 * Provides autocomplete functionality for file system paths.
 * Follows SRP by delegating concerns to specialized hooks.
 * Uses IOC by accepting callbacks as props.
 */
export function PathInputWithSuggestions({
  value,
  onChange,
  onSubmit,
  busy,
}: Props) {
  const { suggestions, show, setShow } = usePathSuggestions({
    query: value,
    enabled: !busy,
  });

  const {
    selectedIndex,
    hoveredIndex,
    setHoveredIndex,
    selectNext,
    selectPrevious,
    resetAll,
  } = useListSelection({
    itemCount: suggestions.length,
    enabled: show && suggestions.length > 0,
  });

  // Reset selection when suggestions change
  useEffect(() => {
    resetAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resetAll]);

  const handleSelectSuggestion = useCallback(
    (suggestion: string) => {
      onChange(suggestion);
      setShow(false);
    },
    [onChange, setShow],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange(e.target.value);
      resetAll();
    },
    [onChange, resetAll],
  );

  const handleInputFocus = useCallback(() => {
    setShow(suggestions.length > 0);
  }, [suggestions.length, setShow]);

  const handleInputBlur = useCallback(() => {
    setShow(false);
  }, [setShow]);

  const { handleKeyDown } = useSuggestionInputNavigation({
    showSuggestions: show,
    suggestions,
    selectedIndex,
    value,
    getSuggestionValue: (s) => s,
    onSelectSuggestion: handleSelectSuggestion,
    onSubmit,
    onSelectNext: selectNext,
    onSelectPrevious: selectPrevious,
    onHideSuggestions: () => setShow(false),
  });

  const handleSuggestionClick = useCallback(
    (suggestion: string) => {
      handleSelectSuggestion(suggestion);
    },
    [handleSelectSuggestion],
  );

  return (
    <div className="relative min-w-0 flex-1">
      <input
        type="text"
        value={value}
        onChange={handleInputChange}
        placeholder="Enter path, e.g. /home/user/Calibre Library"
        onKeyDown={handleKeyDown}
        onFocus={handleInputFocus}
        onBlur={handleInputBlur}
        disabled={!!busy}
        className={cn(
          "w-full bg-surface-a10 px-3 py-2.5 text-sm text-text-a0",
          "rounded-md border border-[var(--color-surface-a20)]",
          "transition-colors duration-200",
          "focus:border-[var(--color-primary-a0)] focus:outline-none",
          "disabled:cursor-not-allowed disabled:opacity-70",
        )}
      />
      {show && suggestions.length > 0 && (
        <div
          className={cn(
            "absolute top-[calc(100%+4px)] right-0 left-0 z-10",
            "max-h-[240px] overflow-y-auto",
            "rounded-md border border-[var(--color-surface-a20)] bg-surface-a0",
            "shadow-[0_4px_16px_rgba(0,0,0,0.3)]",
          )}
        >
          {suggestions.map((suggestion, idx) => (
            <button
              key={suggestion}
              type="button"
              onMouseDown={(e) => {
                e.preventDefault();
                handleSuggestionClick(suggestion);
              }}
              onMouseEnter={() => setHoveredIndex(idx)}
              onMouseLeave={() => setHoveredIndex(-1)}
              className={cn(
                "block w-full bg-transparent px-3 py-2 text-text-a0",
                "border-0 border-[var(--color-surface-a20)] border-b",
                "cursor-pointer select-none text-left text-sm",
                "transition-colors duration-150",
                (idx === hoveredIndex || idx === selectedIndex) &&
                  "bg-surface-tonal-a0",
                idx === suggestions.length - 1 && "border-b-0",
              )}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
