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

import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/forms/Button";
import { ReadingMode } from "@/icons/ReadingMode";
import { cn } from "@/libs/utils";
import { getControlBackgroundColor } from "@/utils/readingTheme";
import type { PageColor } from "./ReadingThemeSettings";

export interface ReaderControlsProps {
  /** Current progress (0.0 to 1.0). */
  progress: number;
  /** Callback when progress slider changes. */
  onProgressChange?: (progress: number) => void;
  /** Whether progress bar is disabled (e.g., locations not ready). */
  isProgressDisabled?: boolean;
  /** Current font size. */
  fontSize?: number;
  /** Callback when font size changes. */
  onFontSizeChange?: (size: number) => void;
  /** Current theme. */
  theme?: "light" | "dark";
  /** Callback when theme changes. */
  onThemeChange?: (theme: "light" | "dark") => void;
  /** Current page color theme. */
  pageColor?: PageColor;
  /** Whether fullscreen is active. */
  isFullscreen?: boolean;
  /** Callback when fullscreen toggles. */
  onFullscreenToggle?: () => void;
  /** Callback when bookmark button is clicked. */
  onBookmark?: () => void;
  /** Callback when annotation button is clicked. */
  onAnnotation?: () => void;
  /** Optional className. */
  className?: string;
}

/**
 * Reader controls component.
 *
 * Common controls for both EPUB and PDF readers.
 * Includes progress slider, font size, theme toggle, fullscreen, and bookmark/annotation buttons.
 * Follows SRP by focusing solely on control UI.
 *
 * Parameters
 * ----------
 * props : ReaderControlsProps
 *     Component props including callbacks for all controls.
 */
export function ReaderControls({
  progress,
  onProgressChange,
  isProgressDisabled = false,
  fontSize = 16,
  onFontSizeChange,
  theme = "light",
  onThemeChange,
  pageColor = "light",
  isFullscreen = false,
  onFullscreenToggle,
  onBookmark,
  onAnnotation,
  className,
}: ReaderControlsProps) {
  const [localProgress, setLocalProgress] = useState(progress);
  const [showTooltip, setShowTooltip] = useState(false);
  const tooltipTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const progressBarRef = useRef<HTMLDivElement>(null);

  // Sync localProgress with progress prop when it changes
  // This ensures the progress bar reflects navigation to persisted location
  useEffect(() => {
    setLocalProgress(progress);
  }, [progress]);

  // Show tooltip when disabled, auto-dismiss when enabled
  useEffect(() => {
    if (isProgressDisabled) {
      setShowTooltip(true);
      // Clear any existing timeout
      if (tooltipTimeoutRef.current) {
        clearTimeout(tooltipTimeoutRef.current);
      }
    } else {
      // Auto-dismiss tooltip after a short delay when enabled
      tooltipTimeoutRef.current = setTimeout(() => {
        setShowTooltip(false);
      }, 2000);
    }

    return () => {
      if (tooltipTimeoutRef.current) {
        clearTimeout(tooltipTimeoutRef.current);
      }
    };
  }, [isProgressDisabled]);

  const handleProgressChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newProgress = parseFloat(e.target.value);
      setLocalProgress(newProgress);
      onProgressChange?.(newProgress);
    },
    [onProgressChange],
  );

  const handleFontSizeDecrease = useCallback(() => {
    const newSize = Math.max(12, fontSize - 2);
    onFontSizeChange?.(newSize);
  }, [fontSize, onFontSizeChange]);

  const handleFontSizeIncrease = useCallback(() => {
    const newSize = Math.min(24, fontSize + 2);
    onFontSizeChange?.(newSize);
  }, [fontSize, onFontSizeChange]);

  const handleThemeToggle = useCallback(() => {
    onThemeChange?.(theme === "light" ? "dark" : "light");
  }, [theme, onThemeChange]);

  return (
    <div
      className={cn("flex items-center justify-between gap-4 p-4", className)}
      style={{ backgroundColor: getControlBackgroundColor(pageColor) }}
    >
      <div
        className="flex items-center gap-2"
        aria-hidden="true"
        style={{ visibility: "hidden" }}
      >
        <Button
          type="button"
          variant="secondary"
          size="small"
          onClick={handleFontSizeDecrease}
          aria-label="Decrease font size"
        >
          <i className="pi pi-minus" />
        </Button>
        <span className="text-sm text-text-a0">{fontSize}px</span>
        <Button
          type="button"
          variant="secondary"
          size="small"
          onClick={handleFontSizeIncrease}
          aria-label="Increase font size"
        >
          <i className="pi pi-plus" />
        </Button>
      </div>

      <div className="relative flex flex-1 items-center gap-2">
        <span
          className={cn(
            "text-xs",
            isProgressDisabled ? "text-text-a60" : "text-text-a40",
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
            onChange={handleProgressChange}
            disabled={isProgressDisabled}
            className={cn(
              "w-full",
              isProgressDisabled && "cursor-not-allowed opacity-50 grayscale",
            )}
            aria-label="Reading progress"
            aria-disabled={isProgressDisabled}
          />
          {showTooltip && isProgressDisabled && (
            <div className="-translate-x-1/2 -mb-6 absolute bottom-full left-1/2 z-10 flex items-center gap-1.5 rounded bg-surface-a20 px-3 py-1.5 text-text-a0 text-xs shadow-lg">
              <ReadingMode className="h-3 w-3" />
              <span>Loading epub data. Please wait...</span>
            </div>
          )}
        </div>
      </div>

      <div
        className="flex items-center gap-2"
        aria-hidden="true"
        style={{ visibility: "hidden" }}
      >
        <Button
          type="button"
          variant="secondary"
          size="small"
          onClick={handleThemeToggle}
          aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
        >
          <i className={theme === "light" ? "pi pi-moon" : "pi pi-sun"} />
        </Button>
        <Button
          type="button"
          variant="secondary"
          size="small"
          onClick={onFullscreenToggle}
          aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
        >
          <i
            className={
              isFullscreen ? "pi pi-window-minimize" : "pi pi-window-maximize"
            }
          />
        </Button>
        {onBookmark && (
          <Button
            type="button"
            variant="secondary"
            size="small"
            onClick={onBookmark}
            aria-label="Add bookmark"
          >
            <i className="pi pi-bookmark" />
          </Button>
        )}
        {onAnnotation && (
          <Button
            type="button"
            variant="secondary"
            size="small"
            onClick={onAnnotation}
            aria-label="Add annotation"
          >
            <i className="pi pi-pencil" />
          </Button>
        )}
      </div>
    </div>
  );
}
