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
import { PAGE_COLOR_CONFIGS } from "../constants/themeSettings";
import type { PageColor } from "../ReadingThemeSettings";

export interface PageColorSelectorProps {
  /** Currently selected page color. */
  selectedColor: PageColor;
  /** Callback when page color changes. */
  onPageColorChange?: (color: PageColor) => void;
  /** Callback when app theme should change. */
  onAppThemeChange?: (theme: "light" | "dark") => void;
  /** Callback when overlay should be hidden. */
  onOverlayHide?: () => void;
}

/**
 * Page color selector component.
 *
 * Displays available page color themes as circular buttons.
 * Follows SRP by handling only page color selection UI.
 * Follows DRY by eliminating repeated button code.
 * Follows IOC by accepting callbacks as props.
 *
 * Parameters
 * ----------
 * props : PageColorSelectorProps
 *     Component props including selected color and change handlers.
 */
export function PageColorSelector({
  selectedColor,
  onPageColorChange,
  onAppThemeChange,
  onOverlayHide,
}: PageColorSelectorProps) {
  const handleColorSelect = (color: PageColor) => {
    const config = PAGE_COLOR_CONFIGS[color];
    onPageColorChange?.(color);
    onAppThemeChange?.(config.appTheme);
    onOverlayHide?.();
  };

  return (
    <div>
      <h3 className="mb-4 font-medium text-sm text-text-a0">Page Color</h3>
      <div className="flex items-center gap-4">
        {(Object.keys(PAGE_COLOR_CONFIGS) as PageColor[]).map((color) => {
          const config = PAGE_COLOR_CONFIGS[color];
          const isSelected = selectedColor === color;

          return (
            <button
              key={color}
              type="button"
              onClick={() => handleColorSelect(color)}
              className={cn(
                "h-12 w-12 cursor-pointer rounded-full border-2 transition-all",
                isSelected
                  ? "border-primary-a0 ring-2 ring-primary-a0 ring-offset-2"
                  : "border-surface-a30 hover:border-surface-a40",
              )}
              style={{
                backgroundColor: config.backgroundColor,
              }}
              aria-label={config.ariaLabel}
              aria-pressed={isSelected}
            />
          );
        })}
      </div>
    </div>
  );
}
