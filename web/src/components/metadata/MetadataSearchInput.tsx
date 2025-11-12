"use client";

import { forwardRef } from "react";
import { TextInput } from "@/components/forms/TextInput";

export interface MetadataSearchInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "onSubmit"> {
  /** Callback when search is triggered (Enter key or button click). */
  onSearch?: (query: string) => void;
  /** Whether search is in progress. */
  isSearching?: boolean;
  /** Whether the input is disabled. */
  disabled?: boolean;
}

/**
 * Search input component for metadata fetching.
 *
 * Follows SRP by focusing solely on search input rendering and interaction.
 * Uses forwardRef for proper ref forwarding (IOC).
 */
export const MetadataSearchInput = forwardRef<
  HTMLInputElement,
  MetadataSearchInputProps
>(({ onSearch, isSearching = false, disabled = false, ...props }, ref) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !disabled && !isSearching) {
      const query = e.currentTarget.value.trim();
      if (query && onSearch) {
        onSearch(query);
      }
    }
  };

  return (
    <div className="relative w-full">
      <TextInput
        ref={ref}
        {...props}
        disabled={disabled || isSearching}
        onKeyDown={handleKeyDown}
        placeholder={props.placeholder || "Search for book metadata..."}
        aria-label="Metadata search query"
      />
      {isSearching && (
        <div
          className="-translate-y-1/2 pointer-events-none absolute top-1/2 right-3 flex items-center"
          aria-hidden="true"
        >
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-transparent border-t-primary-a0" />
        </div>
      )}
    </div>
  );
});

MetadataSearchInput.displayName = "MetadataSearchInput";
