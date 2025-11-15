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

import { useMemo } from "react";
import { FilterSuggestionsDropdown } from "@/components/library/widgets/FilterSuggestionsDropdown";
import { useMultiTextInput } from "@/hooks/useMultiTextInput";
import { usePermissionSuggestions } from "@/hooks/usePermissionSuggestions";
import { cn } from "@/libs/utils";

export interface PermissionMultiTextInputProps {
  /** Label text for the input. */
  label?: string;
  /** Current values. */
  values: string[];
  /** Callback when values change. */
  onChange: (values: string[]) => void;
  /** Placeholder text. */
  placeholder?: string;
  /** Error message to display. */
  error?: string;
  /** Helper text to display. */
  helperText?: string;
  /** Input ID for accessibility. */
  id?: string;
}

/**
 * Multi-text input component for managing permission names with suggestions.
 *
 * Follows SRP by delegating input logic to useMultiTextInput hook.
 * Uses controlled component pattern (IOC via props).
 * Uses DRY by leveraging useMultiTextInput hook.
 */
export function PermissionMultiTextInput({
  label,
  values,
  onChange,
  placeholder = "Add permissions...",
  error,
  helperText,
  id = "permission-multi-text-input",
}: PermissionMultiTextInputProps) {
  // Multi-text input logic (SRP via hook)
  const {
    inputValue,
    setInputValue,
    addSuggestion,
    removeValue,
    handleKeyDown: baseHandleKeyDown,
    handleBlur,
  } = useMultiTextInput({
    values,
    onChange,
    allowDuplicates: false,
  });

  // Permission suggestions (SRP via hook)
  const { suggestions: allSuggestions, isLoading } = usePermissionSuggestions(
    inputValue,
    inputValue.trim().length > 0,
  );

  // Filter out suggestions that are already selected (DRY via useMemo)
  const suggestions = useMemo(
    () =>
      allSuggestions.filter((suggestion) => !values.includes(suggestion.name)),
    [allSuggestions, values],
  );

  // Enhanced keyboard handling with Tab support for suggestions
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    // Handle Tab key to accept first suggestion
    if (e.key === "Tab" && suggestions.length > 0) {
      e.preventDefault();
      const firstSuggestion = suggestions[0];
      if (firstSuggestion) {
        addSuggestion(firstSuggestion.name);
      }
      return;
    }

    // Delegate other keys to base handler
    baseHandleKeyDown(e);
  };

  const shouldShowDropdown =
    inputValue.trim().length > 0 && (isLoading || suggestions.length > 0);

  return (
    <div className="relative flex w-full flex-col gap-2">
      {label && (
        <label
          htmlFor={id}
          className="font-medium text-sm text-text-a10 leading-normal"
        >
          {label}
        </label>
      )}
      <div className="w-full">
        <div
          className={cn(
            "flex min-h-[2.75rem] flex-wrap items-center gap-2 rounded-md border bg-surface-a0 p-2",
            "transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s]",
            "focus-within:border-primary-a0 focus-within:bg-surface-a10",
            "focus-within:shadow-[var(--shadow-focus-ring)]",
            "hover:not(:focus-within):border-surface-a30",
            error && [
              "border-danger-a0",
              "focus-within:border-danger-a0",
              "focus-within:shadow-[var(--shadow-focus-ring-danger)]",
            ],
            !error && "border-surface-a20",
          )}
        >
          {values.map((value) => (
            <span
              key={value}
              className="inline-flex items-center gap-1.5 rounded-md bg-primary-a0 px-3 py-1.5 text-sm text-text-a0 leading-normal"
            >
              {value}
              <button
                type="button"
                className="flex h-4 w-4 items-center justify-center rounded-full border-none bg-transparent p-0 text-sm text-text-a0 leading-none transition-[background-color_0.15s] hover:bg-black/15 focus:bg-black/20 focus:outline-none"
                onClick={() => removeValue(value)}
                aria-label={`Remove ${value}`}
              >
                <i className="pi pi-times" aria-hidden="true" />
              </button>
            </span>
          ))}
          <input
            id={id}
            type="text"
            className="min-w-[120px] flex-1 border-none bg-transparent py-1 font-inherit text-base text-text-a0 leading-normal placeholder:text-text-a40 focus:outline-none"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={handleBlur}
            placeholder={values.length === 0 ? placeholder : ""}
            aria-invalid={error ? "true" : "false"}
            aria-describedby={
              error || helperText
                ? `${id}-${error ? "error" : "helper"}`
                : undefined
            }
          />
        </div>
        {shouldShowDropdown && (
          <FilterSuggestionsDropdown
            suggestions={suggestions}
            isLoading={isLoading}
            onSuggestionClick={(s) => addSuggestion(s.name)}
          />
        )}
      </div>
      {error && (
        <span
          id={`${id}-error`}
          className="text-danger-a10 text-sm leading-normal"
          role="alert"
        >
          {error}
        </span>
      )}
      {helperText && !error && (
        <span
          id={`${id}-helper`}
          className="text-sm text-text-a30 leading-normal"
        >
          {helperText}
        </span>
      )}
    </div>
  );
}
