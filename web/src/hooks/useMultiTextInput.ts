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

import { type KeyboardEvent, useCallback, useState } from "react";

export interface UseMultiTextInputOptions {
  /** Current values. */
  values: string[];
  /** Callback when values change. */
  onChange: (values: string[]) => void;
  /** Whether to allow duplicate values. */
  allowDuplicates?: boolean;
}

export interface UseMultiTextInputReturn {
  /** Current input value. */
  inputValue: string;
  /** Set input value. */
  setInputValue: (value: string) => void;
  /** Add a value from the input field. */
  addValue: () => void;
  /** Add a value from suggestions. */
  addSuggestion: (value: string) => void;
  /** Remove a value. */
  removeValue: (valueToRemove: string) => void;
  /** Handle keyboard events. */
  handleKeyDown: (e: KeyboardEvent<HTMLInputElement>) => void;
  /** Handle input blur (adds value after delay). */
  handleBlur: () => void;
}

/**
 * Hook for managing multi-text input state and operations.
 *
 * Handles input value state, adding/removing values, and keyboard interactions.
 * Follows SRP by focusing solely on multi-text input logic.
 * Follows DRY by centralizing value management patterns.
 * Follows IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UseMultiTextInputOptions
 *     Configuration options for the hook.
 *
 * Returns
 * -------
 * UseMultiTextInputReturn
 *     Object with input state and handlers.
 */
export function useMultiTextInput(
  options: UseMultiTextInputOptions,
): UseMultiTextInputReturn {
  const { values, onChange, allowDuplicates = false } = options;
  const [inputValue, setInputValue] = useState("");

  const addValueInternal = useCallback(
    (value: string) => {
      const trimmed = value.trim();
      if (!trimmed) {
        return false;
      }

      if (!allowDuplicates && values.includes(trimmed)) {
        return false;
      }

      onChange([...values, trimmed]);
      setInputValue("");
      return true;
    },
    [values, onChange, allowDuplicates],
  );

  const addValue = useCallback(() => {
    addValueInternal(inputValue);
  }, [inputValue, addValueInternal]);

  const addSuggestion = useCallback(
    (value: string) => {
      addValueInternal(value);
    },
    [addValueInternal],
  );

  const removeValue = useCallback(
    (valueToRemove: string) => {
      onChange(values.filter((value) => value !== valueToRemove));
    },
    [values, onChange],
  );

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
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
    },
    [inputValue, values, onChange, addValue],
  );

  const handleBlur = useCallback(() => {
    setTimeout(() => addValue(), 150);
  }, [addValue]);

  return {
    inputValue,
    setInputValue,
    addValue,
    addSuggestion,
    removeValue,
    handleKeyDown,
    handleBlur,
  };
}
