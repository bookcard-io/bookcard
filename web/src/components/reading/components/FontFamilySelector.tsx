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

import { cn } from "@/libs/utils";
import { AVAILABLE_FONT_FAMILIES } from "../constants/themeSettings";
import type { FontFamily } from "../ReadingThemeSettings";

export interface FontFamilySelectorProps {
  /** Currently selected font family. */
  selectedFamily: FontFamily;
  /** Callback when font family changes. */
  onFamilyChange: (family: FontFamily) => void;
}

/**
 * Font family selector component.
 *
 * Displays available font families in a grid layout with preview.
 * Follows SRP by handling only font family selection UI.
 * Follows IOC by accepting callbacks as props.
 *
 * Parameters
 * ----------
 * props : FontFamilySelectorProps
 *     Component props including selected family and change handler.
 */
export function FontFamilySelector({
  selectedFamily,
  onFamilyChange,
}: FontFamilySelectorProps) {
  return (
    <div className="mb-8">
      <h3 className="mb-4 font-medium text-sm text-text-a0">Font</h3>
      <div className="grid grid-cols-3 gap-3">
        {AVAILABLE_FONT_FAMILIES.map((family) => {
          const isSelected = selectedFamily === family;
          return (
            <button
              key={family}
              type="button"
              onClick={() => onFamilyChange(family)}
              className={cn(
                "flex flex-col items-center gap-2 rounded-md border p-2 transition-colors",
                isSelected
                  ? "border-primary-a0 bg-primary-a0/10"
                  : "border-surface-a20 bg-surface-a10 hover:border-surface-a30 hover:bg-surface-a20",
              )}
              aria-label={`Select ${family} font`}
              aria-pressed={isSelected}
            >
              <div
                className={cn(
                  "flex h-12 w-12 items-center justify-center rounded border text-3xl",
                  isSelected
                    ? "border-primary-a0 bg-primary-a0/20 text-primary-a0"
                    : "border-surface-a30 bg-surface-a20 text-text-a40",
                )}
                style={{
                  fontFamily: `${family}, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`,
                }}
              >
                Aa
              </div>
              <span
                className={cn(
                  "text-xs",
                  isSelected ? "text-primary-a0" : "text-text-a40",
                )}
              >
                {family}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
