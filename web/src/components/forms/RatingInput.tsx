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

import { RatingStars } from "./RatingStars";

export interface RatingInputProps {
  /** Label text for the input. */
  label?: string;
  /** Current rating value (0-5). */
  value: number | null;
  /** Callback when rating changes. */
  onChange: (rating: number | null) => void;
  /** Error message to display. */
  error?: string;
  /** Helper text to display. */
  helperText?: string;
  /** Input ID for accessibility. */
  id?: string;
  /** Whether the input is disabled. */
  disabled?: boolean;
}

/**
 * Rating input component for selecting a rating from 0-5.
 *
 * Follows SRP by focusing solely on rating selection.
 * Uses controlled component pattern (IOC via props).
 * Reuses RatingStars component for star rendering (DRY).
 */
export function RatingInput({
  label,
  value,
  onChange,
  error,
  helperText,
  id = "rating-input",
  disabled = false,
}: RatingInputProps) {
  const handleStarClick = (rating: number) => {
    if (value === rating) {
      // Clicking the same rating clears it
      onChange(null);
    } else {
      onChange(rating);
    }
  };

  return (
    <div className="flex w-full flex-col gap-2">
      {label && (
        <label
          htmlFor={id}
          className="font-medium text-sm text-text-a10 leading-normal"
        >
          {label}
        </label>
      )}
      <div
        role="radiogroup"
        aria-label={label || "Rating"}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={
          error || helperText
            ? `${id}-${error ? "error" : "helper"}`
            : undefined
        }
      >
        <RatingStars
          value={value}
          interactive
          onStarClick={handleStarClick}
          disabled={disabled}
        />
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
