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
import { cn } from "@/libs/utils";

export interface Identifier {
  type: string;
  val: string;
}

export interface IdentifierInputProps {
  /** Label text for the input. */
  label?: string;
  /** Current identifiers. */
  identifiers: Identifier[];
  /** Callback when identifiers change. */
  onChange: (identifiers: Identifier[]) => void;
  /** Error message to display. */
  error?: string;
  /** Helper text to display. */
  helperText?: string;
  /** Input ID for accessibility. */
  id?: string;
}

/**
 * Identifier input component for managing book identifiers (ISBN, DOI, etc.).
 *
 * Follows SRP by focusing solely on identifier management.
 * Uses controlled component pattern (IOC via props).
 */
export function IdentifierInput({
  label,
  identifiers,
  onChange,
  error,
  helperText,
  id = "identifier-input",
}: IdentifierInputProps) {
  const [typeValue, setTypeValue] = useState("isbn");
  const [valValue, setValValue] = useState("");

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addIdentifier();
    }
  };

  const addIdentifier = () => {
    const trimmed = valValue.trim();
    if (trimmed) {
      const newIdentifier: Identifier = {
        type: typeValue.trim() || "isbn",
        val: trimmed,
      };
      // Check for duplicates
      const isDuplicate = identifiers.some(
        (id) => id.type === newIdentifier.type && id.val === newIdentifier.val,
      );
      if (!isDuplicate) {
        onChange([...identifiers, newIdentifier]);
        setValValue("");
      }
    }
  };

  const removeIdentifier = (index: number) => {
    onChange(identifiers.filter((_, i) => i !== index));
  };

  return (
    <div className="flex w-full flex-col gap-2">
      {label && (
        <label
          htmlFor={`${id}-val`}
          className="font-medium text-sm text-text-a10 leading-normal"
        >
          {label}
        </label>
      )}
      <div className="flex w-full flex-col gap-2">
        {identifiers.map((identifier, index) => (
          <div
            key={`${identifier.type}-${identifier.val}-${index}`}
            className="flex items-center gap-3 rounded-lg border border-surface-a20 bg-surface-a10 px-3 py-2"
          >
            <span className="min-w-16 font-semibold text-primary-a0 text-xs uppercase">
              {identifier.type}
            </span>
            <span className="flex-1 text-sm text-text-a0">
              {identifier.val}
            </span>
            <button
              type="button"
              className="flex h-6 w-6 items-center justify-center rounded-full border-none bg-transparent p-1 text-sm text-text-a30 transition-[background-color_0.15s,color_0.15s] hover:bg-danger-a20 hover:text-danger-a10 focus:bg-danger-a20 focus:text-danger-a10 focus:outline-none"
              onClick={() => removeIdentifier(index)}
              aria-label={`Remove ${identifier.type} ${identifier.val}`}
            >
              <i className="pi pi-times" aria-hidden="true" />
            </button>
          </div>
        ))}
        <div className="flex items-center gap-2">
          <select
            id={`${id}-type`}
            className={cn(
              "flex-[0_0_8rem] cursor-pointer rounded-lg border border-surface-a20 bg-surface-a0 px-4 py-3",
              "font-inherit text-base text-text-a0 leading-normal",
              "transition-[border-color_0.2s,background-color_0.2s]",
              "focus:border-primary-a0 focus:bg-surface-a10 focus:outline-none",
              "hover:not(:focus):border-surface-a30",
            )}
            value={typeValue}
            onChange={(e) => setTypeValue(e.target.value)}
          >
            <option value="isbn">ISBN</option>
            <option value="doi">DOI</option>
            <option value="asin">ASIN</option>
            <option value="goodreads">Goodreads</option>
            <option value="google">Google Books</option>
            <option value="amazon">Amazon</option>
            <option value="other">Other</option>
          </select>
          <input
            id={`${id}-val`}
            type="text"
            className={cn(
              "flex-1 rounded-lg border bg-surface-a0 px-4 py-3",
              "font-inherit text-base text-text-a0 leading-normal",
              "transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s]",
              "placeholder:text-text-a40",
              "focus:border-primary-a0 focus:bg-surface-a10 focus:outline-none",
              "focus:shadow-[var(--shadow-focus-ring)]",
              "hover:not(:focus):border-surface-a30",
              error && [
                "border-danger-a0",
                "focus:border-danger-a0",
                "focus:shadow-[var(--shadow-focus-ring-danger)]",
              ],
              !error && "border-surface-a20",
            )}
            value={valValue}
            onChange={(e) => setValValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={addIdentifier}
            placeholder="Enter identifier value..."
            aria-invalid={error ? "true" : "false"}
            aria-describedby={
              error || helperText
                ? `${id}-${error ? "error" : "helper"}`
                : undefined
            }
          />
        </div>
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
