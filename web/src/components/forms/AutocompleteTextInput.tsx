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

import { forwardRef, useEffect, useRef, useState } from "react";
import { FilterSuggestionsDropdown } from "@/components/library/widgets/FilterSuggestionsDropdown";
import { useFilterSuggestions } from "@/hooks/useFilterSuggestions";
import { cn } from "@/libs/utils";

export interface AutocompleteTextInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  /** Label text for the input. */
  label?: string;
  /** Error message to display. */
  error?: string;
  /** Helper text to display below input. */
  helperText?: string;
  /** Filter type to query suggestions for. */
  filterType: string;
}

export const AutocompleteTextInput = forwardRef<
  HTMLInputElement,
  AutocompleteTextInputProps
>(
  (
    {
      label,
      error,
      helperText,
      className,
      filterType,
      value,
      onChange,
      id,
      ...props
    },
    ref,
  ) => {
    const [query, setQuery] = useState(String(value ?? ""));
    const [isFocused, setIsFocused] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
      setQuery(String(value ?? ""));
    }, [value]);

    const { suggestions, isLoading } = useFilterSuggestions({
      query,
      filterType,
      enabled: isFocused && query.trim().length > 0,
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setQuery(e.target.value);
      onChange?.(e);
    };

    const handleSuggestionClick = (name: string) => {
      setQuery(name);
      const syntheticEvent = {
        target: { value: name },
      } as unknown as React.ChangeEvent<HTMLInputElement>;
      onChange?.(syntheticEvent);
      setIsFocused(false);
    };

    const shouldShowDropdown =
      isFocused &&
      query.trim().length > 0 &&
      (isLoading || suggestions.length > 0);

    return (
      <div className="relative flex w-full flex-col gap-2" ref={containerRef}>
        {label && (
          <label
            htmlFor={id}
            className="font-medium text-sm text-text-a10 leading-normal"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          type="text"
          className={cn(
            "w-full rounded-lg border border-surface-a20 bg-surface-a0 px-4 py-3",
            "font-inherit text-base text-text-a0 leading-normal",
            "transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s]",
            "placeholder:text-text-a40",
            "hover:not(:focus):border-surface-a30",
            "focus:border-primary-a0 focus:bg-surface-a10 focus:outline-none",
            "focus:shadow-[var(--shadow-focus-ring)]",
            "disabled:cursor-not-allowed disabled:opacity-50",
            error && [
              "border-danger-a0",
              "focus:border-danger-a0 focus:shadow-[var(--shadow-focus-ring-danger)]",
            ],
            className,
          )}
          value={query}
          onChange={handleChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setTimeout(() => setIsFocused(false), 150)}
          aria-invalid={error ? "true" : "false"}
          aria-describedby={
            error || helperText
              ? `${id}-${error ? "error" : "helper"}`
              : undefined
          }
          {...props}
        />
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
        {shouldShowDropdown && (
          <FilterSuggestionsDropdown
            suggestions={suggestions}
            isLoading={isLoading}
            onSuggestionClick={(s) => handleSuggestionClick(s.name)}
          />
        )}
      </div>
    );
  },
);

AutocompleteTextInput.displayName = "AutocompleteTextInput";
