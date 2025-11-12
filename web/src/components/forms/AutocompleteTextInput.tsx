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
import styles from "./TextInput.module.scss";

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
      <div className={styles.container} ref={containerRef}>
        {label && (
          <label htmlFor={id} className={styles.label}>
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          type="text"
          className={`${styles.input} ${error ? styles.inputError : ""} ${className || ""}`}
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
          <span id={`${id}-error`} className={styles.error} role="alert">
            {error}
          </span>
        )}
        {helperText && !error && (
          <span id={`${id}-helper`} className={styles.helperText}>
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
