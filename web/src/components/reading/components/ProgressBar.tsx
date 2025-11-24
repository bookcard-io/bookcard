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

import { useRef } from "react";
import { ReadingMode } from "@/icons/ReadingMode";
import { cn } from "@/libs/utils";
import { useProgressBar } from "../hooks/useProgressBar";

export interface ProgressBarProps {
  /** Current progress (0.0 to 1.0). */
  progress: number;
  /** Callback when progress slider changes. */
  onProgressChange?: (progress: number) => void;
  /** Whether progress bar is disabled (e.g., locations not ready). */
  isDisabled?: boolean;
}

/**
 * Progress bar component with loading tooltip.
 *
 * Follows SRP by focusing solely on progress display and interaction.
 * Follows IOC by accepting callbacks for state changes.
 *
 * Parameters
 * ----------
 * props : ProgressBarProps
 *     Component props including progress value and change handler.
 */
export function ProgressBar({
  progress,
  onProgressChange,
  isDisabled = false,
}: ProgressBarProps) {
  const progressBarRef = useRef<HTMLDivElement>(null);
  const { localProgress, showTooltip, handleProgressChange } = useProgressBar(
    progress,
    isDisabled,
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newProgress = handleProgressChange(e);
    onProgressChange?.(newProgress);
  };

  return (
    <div className="relative flex flex-1 items-center gap-2 max-w-[80vw]">
      <span
        className={cn(
          "text-xs",
          isDisabled ? "text-text-a60" : "text-text-a40",
        )}
      >
        {Math.round(localProgress * 100)}%
      </span>
      <div ref={progressBarRef} className="relative flex-1">
        <input
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={localProgress}
          onChange={handleChange}
          disabled={isDisabled}
          className={cn(
            "w-full",
            isDisabled && "cursor-not-allowed opacity-50 grayscale",
          )}
          aria-label="Reading progress"
          aria-disabled={isDisabled}
        />
        {showTooltip && isDisabled && (
          <div className="-translate-x-1/2 -mb-6 absolute bottom-full left-1/2 z-10 flex items-center gap-1.5 rounded bg-surface-a20 px-3 py-1.5 text-text-a0 text-xs shadow-lg">
            <ReadingMode className="h-3 w-3" />
            <span>Loading epub data. Please wait...</span>
          </div>
        )}
      </div>
    </div>
  );
}
