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

import { useCallback } from "react";
import {
  FONT_SIZE_MAX,
  FONT_SIZE_MIN,
  FONT_SIZE_STEP,
} from "../constants/themeSettings";

export interface FontSizeSliderProps {
  /** Current font size in pixels. */
  fontSize: number;
  /** Callback when font size changes. */
  onFontSizeChange: (size: number) => void;
}

/**
 * Font size slider component.
 *
 * Displays a range input for adjusting font size with visual feedback.
 * Follows SRP by handling only font size selection UI.
 * Follows IOC by accepting callbacks as props.
 *
 * Parameters
 * ----------
 * props : FontSizeSliderProps
 *     Component props including current size and change handler.
 */
export function FontSizeSlider({
  fontSize,
  onFontSizeChange,
}: FontSizeSliderProps) {
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newSize = parseFloat(e.target.value);
      onFontSizeChange(newSize);
    },
    [onFontSizeChange],
  );

  const progressPercentage =
    ((fontSize - FONT_SIZE_MIN) / (FONT_SIZE_MAX - FONT_SIZE_MIN)) * 100;

  return (
    <div className="mb-8">
      <h3 className="mb-4 font-medium text-sm text-text-a0">Font Size</h3>
      <div className="flex items-center gap-4">
        <span className="text-sm text-text-a40">A</span>
        <div className="relative flex-1">
          <input
            type="range"
            min={FONT_SIZE_MIN}
            max={FONT_SIZE_MAX}
            step={FONT_SIZE_STEP}
            value={fontSize}
            onChange={handleChange}
            className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-surface-a20 accent-primary-a0"
            style={{
              background: `linear-gradient(to right, var(--clr-primary-a0) 0%, var(--clr-primary-a0) ${progressPercentage}%, var(--clr-surface-a20) ${progressPercentage}%, var(--clr-surface-a20) 100%)`,
            }}
            aria-label="Font size"
          />
        </div>
        <span className="text-2xl text-text-a40">A</span>
        <span className="min-w-[3rem] text-right text-sm text-text-a0">
          {fontSize}px
        </span>
      </div>
    </div>
  );
}
