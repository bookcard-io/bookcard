// Copyright (C) 2025 khoa and others
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

import { useEffect, useRef } from "react";
import { TextInput } from "@/components/forms/TextInput";
import { ThemeSettingsOverlay } from "./components/ThemeSettingsOverlay";
import { ThemeSettingsPanel } from "./components/ThemeSettingsPanel";
import { useThemeSettingsPanel } from "./hooks/useThemeSettingsPanel";

export interface ReadingSearchPanelProps {
  /** Whether the panel is open. */
  isOpen: boolean;
  /** Callback when the panel should be closed. */
  onClose: () => void;
  /** Optional className. */
  className?: string;
}

/**
 * Slide-out search panel for the reading page.
 *
 * Allows users to search for words or phrases in the book.
 * Slides in from the right side with smooth animation.
 *
 * Follows SRP by delegating to specialized components.
 * Follows SOC by separating concerns into components and hooks.
 * Follows IOC by accepting callbacks as props.
 * Follows DRY by reusing shared components.
 *
 * Parameters
 * ----------
 * props : ReadingSearchPanelProps
 *     Component props including open state and callbacks.
 */
export function ReadingSearchPanel({
  isOpen,
  onClose,
  className,
}: ReadingSearchPanelProps) {
  const { showOverlay } = useThemeSettingsPanel({
    isOpen,
    onClose,
  });

  const searchInputRef = useRef<HTMLInputElement>(null);

  // Focus the input when the panel opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      // Small delay to ensure the panel animation has started
      const timeoutId = setTimeout(() => {
        searchInputRef.current?.focus();
      }, 100);
      return () => clearTimeout(timeoutId);
    }
    return undefined;
  }, [isOpen]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      // No-op for now
    }
  };

  return (
    <>
      <ThemeSettingsOverlay
        isVisible={showOverlay && isOpen}
        onClick={onClose}
      />
      <ThemeSettingsPanel
        isOpen={isOpen}
        onClose={onClose}
        className={className}
        title="Search in book"
        ariaLabel="Search in book"
        closeAriaLabel="Close search panel"
      >
        <div className="flex flex-col gap-4">
          <TextInput
            ref={searchInputRef}
            id="book-search-input"
            placeholder="Search for a word or a phrase"
            onKeyDown={handleKeyDown}
          />
        </div>
      </ThemeSettingsPanel>
    </>
  );
}
