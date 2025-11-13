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

import { TextInput } from "@/components/forms/TextInput";

export interface CoverUrlInputProps {
  /** Input value. */
  value: string;
  /** Whether input is disabled. */
  disabled?: boolean;
  /** Error message to display. */
  error?: string | null;
  /** Ref for the input element. */
  inputRef: React.RefObject<HTMLInputElement | null>;
  /** Handler for value changes. */
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  /** Handler for keyboard events. */
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
}

/**
 * Cover URL input component.
 *
 * Displays an input field for entering a cover image URL.
 * Follows SRP by focusing solely on URL input presentation.
 *
 * Parameters
 * ----------
 * props : CoverUrlInputProps
 *     Component props including value, handlers, and state.
 */
export function CoverUrlInput({
  value,
  disabled,
  error,
  inputRef,
  onChange,
  onKeyDown,
}: CoverUrlInputProps) {
  return (
    <div className="mt-2">
      <TextInput
        ref={inputRef}
        id="cover-url-input"
        value={value}
        onChange={onChange}
        onKeyDown={onKeyDown}
        placeholder="Paste URL and press Enter"
        disabled={disabled}
        error={error || undefined}
        autoFocus
      />
    </div>
  );
}
