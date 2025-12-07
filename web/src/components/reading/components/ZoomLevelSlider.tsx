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

import { useCallback } from "react";

const ZOOM_LEVEL_MIN = 0.5;
const ZOOM_LEVEL_MAX = 3.0;
const ZOOM_LEVEL_STEP = 0.1;

export interface ZoomLevelSliderProps {
  /** Current zoom level (0.5 to 3.0). */
  zoomLevel: number;
  /** Callback when zoom level changes. */
  onZoomLevelChange: (level: number) => void;
}

/**
 * Zoom level slider component.
 *
 * Displays a range input for adjusting zoom level with visual feedback.
 * Follows SRP by handling only zoom level selection UI.
 * Follows IOC by accepting callbacks as props.
 *
 * Parameters
 * ----------
 * props : ZoomLevelSliderProps
 *     Component props including current zoom level and change handler.
 */
export function ZoomLevelSlider({
  zoomLevel,
  onZoomLevelChange,
}: ZoomLevelSliderProps) {
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newLevel = parseFloat(e.target.value);
      onZoomLevelChange(newLevel);
    },
    [onZoomLevelChange],
  );

  const progressPercentage =
    ((zoomLevel - ZOOM_LEVEL_MIN) / (ZOOM_LEVEL_MAX - ZOOM_LEVEL_MIN)) * 100;

  return (
    <div className="mb-8">
      <h3 className="mb-4 font-medium text-sm text-text-a0">Zoom Level</h3>
      <div className="flex items-center gap-4">
        <span className="text-sm text-text-a40">0.5x</span>
        <div className="relative flex-1">
          <input
            type="range"
            min={ZOOM_LEVEL_MIN}
            max={ZOOM_LEVEL_MAX}
            step={ZOOM_LEVEL_STEP}
            value={zoomLevel}
            onChange={handleChange}
            className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-surface-a20 accent-primary-a0"
            style={{
              background: `linear-gradient(to right, var(--clr-primary-a0) 0%, var(--clr-primary-a0) ${progressPercentage}%, var(--clr-surface-a20) ${progressPercentage}%, var(--clr-surface-a20) 100%)`,
            }}
            aria-label="Zoom level"
          />
        </div>
        <span className="text-sm text-text-a40">3.0x</span>
        <span className="min-w-[3rem] text-right text-sm text-text-a0">
          {zoomLevel.toFixed(1)}x
        </span>
      </div>
    </div>
  );
}
