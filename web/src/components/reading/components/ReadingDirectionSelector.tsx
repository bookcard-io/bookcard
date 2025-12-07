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

import { cn } from "@/libs/utils";
import type { ComicReadingDirection } from "../ComicReader";

export interface ReadingDirectionSelectorProps {
  /** Currently selected reading direction. */
  selectedDirection: ComicReadingDirection;
  /** Callback when reading direction changes. */
  onDirectionChange: (direction: ComicReadingDirection) => void;
}

/**
 * Reading direction selector component.
 *
 * Displays available reading directions (LTR, RTL, vertical) as buttons.
 * Follows SRP by handling only reading direction selection UI.
 * Follows IOC by accepting callbacks as props.
 *
 * Parameters
 * ----------
 * props : ReadingDirectionSelectorProps
 *     Component props including selected direction and change handler.
 */
export function ReadingDirectionSelector({
  selectedDirection,
  onDirectionChange,
}: ReadingDirectionSelectorProps) {
  const directions: Array<{
    direction: ComicReadingDirection;
    label: string;
    icon: string;
  }> = [
    { direction: "ltr", label: "LTR", icon: "→" },
    { direction: "rtl", label: "RTL", icon: "←" },
    { direction: "vertical", label: "Vertical", icon: "↓" },
  ];

  return (
    <div className="mb-8">
      <h3 className="mb-4 font-medium text-sm text-text-a0">
        Reading Direction
      </h3>
      <div className="grid grid-cols-3 gap-3">
        {directions.map(({ direction, label, icon }) => {
          const isSelected = selectedDirection === direction;
          return (
            <button
              key={direction}
              type="button"
              onClick={() => onDirectionChange(direction)}
              className={cn(
                "flex flex-col items-center gap-2 rounded-md border p-2 transition-colors",
                isSelected
                  ? "border-primary-a0 bg-primary-a0/10"
                  : "border-surface-a20 bg-surface-a10 hover:border-surface-a30 hover:bg-surface-a20",
              )}
              aria-label={`Select ${label} reading direction`}
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
                {icon}
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
