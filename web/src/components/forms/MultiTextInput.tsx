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

import { type KeyboardEvent, useState } from "react";
import { FilterSuggestionsDropdown } from "@/components/library/widgets/FilterSuggestionsDropdown";
import { useFilterSuggestions } from "@/hooks/useFilterSuggestions";
import styles from "./MultiTextInput.module.scss";

export interface MultiTextInputProps {
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
  /** Optional filter type to enable autocomplete suggestions. */
  filterType?: string;
}

/**
 * Multi-text input component for managing a list of text values (e.g., authors).
 *
 * Follows SRP by focusing solely on multi-value text management.
 * Uses controlled component pattern (IOC via props).
 */
export function MultiTextInput({
  label,
  values,
  onChange,
  placeholder = "Add items...",
  error,
  helperText,
  id = "multi-text-input",
  filterType,
}: MultiTextInputProps) {
  const [inputValue, setInputValue] = useState("");

  const { suggestions, isLoading } = useFilterSuggestions({
    query: inputValue,
    filterType: filterType || "",
    enabled: Boolean(filterType) && inputValue.trim().length > 0,
  });

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addValue();
    } else if (
      e.key === "Backspace" &&
      inputValue === "" &&
      values.length > 0
    ) {
      // Remove last value when backspace is pressed on empty input
      onChange(values.slice(0, -1));
    }
  };

  const addValue = () => {
    const trimmed = inputValue.trim();
    if (trimmed && !values.includes(trimmed)) {
      onChange([...values, trimmed]);
      setInputValue("");
    }
  };

  const addSuggestion = (name: string) => {
    if (!values.includes(name)) {
      onChange([...values, name]);
    }
    setInputValue("");
  };

  const removeValue = (valueToRemove: string) => {
    onChange(values.filter((value) => value !== valueToRemove));
  };

  const shouldShowDropdown =
    Boolean(filterType) &&
    inputValue.trim().length > 0 &&
    (isLoading || suggestions.length > 0);

  return (
    <div className={styles.container}>
      {label && (
        <label htmlFor={id} className={styles.label}>
          {label}
        </label>
      )}
      <div className={styles.inputWrapper}>
        <div className={styles.valuesContainer}>
          {values.map((value) => (
            <span key={value} className={styles.value}>
              {value}
              <button
                type="button"
                className={styles.removeButton}
                onClick={() => removeValue(value)}
                aria-label={`Remove ${value}`}
              >
                ×
              </button>
            </span>
          ))}
          <input
            id={id}
            type="text"
            className={`${styles.input} ${error ? styles.inputError : ""}`}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={() => setTimeout(() => addValue(), 150)}
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
        <span id={`${id}-error`} className={styles.error} role="alert">
          {error}
        </span>
      )}
      {helperText && !error && (
        <span id={`${id}-helper`} className={styles.helperText}>
          {helperText}
        </span>
      )}
    </div>
  );
}
