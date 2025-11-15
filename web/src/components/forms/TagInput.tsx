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
import { cn } from "@/libs/utils";
import type { FilterSuggestionsService } from "@/services/filterSuggestionsService";

export interface TagInputProps {
  /** Label text for the input. */
  label?: string;
  /** Current tags. */
  tags: string[];
  /** Callback when tags change. */
  onChange: (tags: string[]) => void;
  /** Placeholder text. */
  placeholder?: string;
  /** Error message to display. */
  error?: string;
  /** Helper text to display. */
  helperText?: string;
  /** Input ID for accessibility. */
  id?: string;
  /** Optional filter type to enable autocomplete suggestions (e.g., 'genre'). */
  filterType?: string;
  /** Optional custom service for fetching suggestions (for IOC). */
  suggestionsService?: FilterSuggestionsService;
  /** Maximum number of tags allowed (default: unlimited). */
  maxTags?: number;
}

/**
 * Tag input component for managing a list of tags.
 *
 * Follows SRP by focusing solely on tag management.
 * Uses controlled component pattern (IOC via props).
 */
export function TagInput({
  label,
  tags,
  onChange,
  placeholder = "Add tags...",
  error,
  helperText,
  id = "tag-input",
  filterType,
  suggestionsService,
  maxTags,
}: TagInputProps) {
  const [inputValue, setInputValue] = useState("");

  const { suggestions, isLoading } = useFilterSuggestions({
    query: inputValue,
    filterType: filterType || "",
    enabled: Boolean(filterType) && inputValue.trim().length > 0,
    service: suggestionsService,
  });

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag();
    } else if (e.key === "Backspace" && inputValue === "" && tags.length > 0) {
      // Remove last tag when backspace is pressed on empty input
      onChange(tags.slice(0, -1));
    }
  };

  const addTag = () => {
    const trimmed = inputValue.trim();
    if (trimmed && !tags.includes(trimmed)) {
      // Check maxTags limit
      if (maxTags !== undefined && tags.length >= maxTags) {
        setInputValue("");
        return;
      }
      onChange([...tags, trimmed]);
      setInputValue("");
    }
  };

  const addSuggestion = (name: string) => {
    if (!tags.includes(name)) {
      // Check maxTags limit
      if (maxTags !== undefined && tags.length >= maxTags) {
        setInputValue("");
        return;
      }
      onChange([...tags, name]);
    }
    setInputValue("");
  };

  const removeTag = (tagToRemove: string) => {
    onChange(tags.filter((tag) => tag !== tagToRemove));
  };

  const shouldShowDropdown =
    Boolean(filterType) &&
    inputValue.trim().length > 0 &&
    (isLoading || suggestions.length > 0);

  const canAddMoreTags = maxTags === undefined || tags.length < maxTags;

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
            "focus-within:shadow-[0_0_0_3px_rgba(144,170,249,0.1)]",
            "hover:not(:focus-within):border-surface-a30",
            error && [
              "border-danger-a0",
              "focus-within:border-danger-a0",
              "focus-within:shadow-[0_0_0_3px_rgba(156,33,33,0.1)]",
            ],
            !error && "border-surface-a20",
          )}
        >
          {tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1.5 rounded-md bg-primary-a0 px-3 py-1.5 text-sm text-text-a0 leading-normal"
            >
              {tag}
              <button
                type="button"
                className="flex h-4 w-4 items-center justify-center rounded-full border-none bg-transparent p-0 text-sm text-text-a0 leading-none transition-[background-color_0.15s] hover:bg-black/15 focus:bg-black/20 focus:outline-none"
                onClick={() => removeTag(tag)}
                aria-label={`Remove tag ${tag}`}
              >
                <i className="pi pi-times" aria-hidden="true" />
              </button>
            </span>
          ))}
          {canAddMoreTags && (
            <input
              id={id}
              type="text"
              className="min-w-[120px] flex-1 border-none bg-transparent py-1 font-inherit text-base text-text-a0 leading-normal placeholder:text-text-a40 focus:outline-none"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onBlur={() => setTimeout(() => addTag(), 150)}
              placeholder={tags.length === 0 ? placeholder : ""}
              aria-invalid={error ? "true" : "false"}
              aria-describedby={
                error || helperText
                  ? `${id}-${error ? "error" : "helper"}`
                  : undefined
              }
            />
          )}
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
