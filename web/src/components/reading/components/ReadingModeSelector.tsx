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

import { BookOpenPageVariantOutline } from "@/icons/BookOpenPageVariantOutline";
import { PageScroll } from "@/icons/PageScroll";
import { Webtoon } from "@/icons/Webtoon";
import { cn } from "@/libs/utils";
import type { ComicReadingMode } from "../ComicReader";

export interface ReadingModeSelectorProps {
  /** Currently selected reading mode. */
  selectedMode: ComicReadingMode;
  /** Callback when reading mode changes. */
  onModeChange: (mode: ComicReadingMode) => void;
}

/**
 * Reading mode selector component.
 *
 * Displays available reading modes (paged, continuous, webtoon) as buttons.
 * Follows SRP by handling only reading mode selection UI.
 * Follows IOC by accepting callbacks as props.
 *
 * Parameters
 * ----------
 * props : ReadingModeSelectorProps
 *     Component props including selected mode and change handler.
 */
export function ReadingModeSelector({
  selectedMode,
  onModeChange,
}: ReadingModeSelectorProps) {
  const modes: Array<{
    mode: ComicReadingMode;
    label: string;
    Icon: React.ElementType;
  }> = [
    { mode: "paged", label: "Paged", Icon: BookOpenPageVariantOutline },
    { mode: "continuous", label: "Continuous", Icon: PageScroll },
    { mode: "webtoon", label: "Webtoon", Icon: Webtoon },
  ];

  return (
    <div className="mb-8">
      <h3 className="mb-4 font-medium text-sm text-text-a0">Reading Mode</h3>
      <div className="grid grid-cols-3 gap-3">
        {modes.map(({ mode, label, Icon }) => {
          const isSelected = selectedMode === mode;
          return (
            <button
              key={mode}
              type="button"
              onClick={() => onModeChange(mode)}
              className={cn(
                "flex flex-col items-center gap-2 rounded-md border p-2 transition-colors",
                isSelected
                  ? "border-primary-a0 bg-primary-a0/10"
                  : "border-surface-a20 bg-surface-a10 hover:border-surface-a30 hover:bg-surface-a20",
              )}
              aria-label={`Select ${label} reading mode`}
              aria-pressed={isSelected}
            >
              <div
                className={cn(
                  "flex h-12 w-12 items-center justify-center rounded border text-2xl",
                  isSelected
                    ? "border-primary-a0 bg-primary-a0/20 text-primary-a0"
                    : "border-surface-a30 bg-surface-a20 text-text-a40",
                )}
              >
                <Icon className="h-6 w-6" />
              </div>
              <span
                className={cn(
                  "text-xs",
                  isSelected ? "text-primary-a0" : "text-text-a40",
                )}
              >
                {label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
