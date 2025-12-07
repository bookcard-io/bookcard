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
import { getControlBackgroundColor } from "@/utils/readingTheme";
import { PagingInfoDisplay } from "./components/PagingInfoDisplay";
import { ProgressBar } from "./components/ProgressBar";
import type { PageColor } from "./ReadingThemeSettings";

export interface PagingInfo {
  /** Current page number. */
  currentPage: number;
  /** Total pages in the book. */
  totalPages: number;
  /** Current chapter label (if available). */
  chapterLabel?: string;
  /** Total pages in current chapter (if available). */
  chapterTotalPages?: number;
}

export interface ReaderControlsProps {
  /** Current progress (0.0 to 1.0). */
  progress: number;
  /** Callback when progress slider changes. */
  onProgressChange?: (progress: number) => void;
  /** Whether progress bar is disabled (e.g., locations not ready). */
  isProgressDisabled?: boolean;
  /** Whether EPUB data is currently loading. */
  isLoadingEpubData?: boolean;
  /** Current page color theme. */
  pageColor?: PageColor;
  /** Paging information for display. */
  pagingInfo?: PagingInfo;
  /** Optional className. */
  className?: string;
}

/**
 * Reader controls component.
 *
 * Common controls for both EPUB and PDF readers.
 * Orchestrates sub-components for progress and paging information.
 * Follows SRP by delegating to specialized sub-components.
 * Follows IOC by accepting callbacks for all state changes.
 * Follows SOC by separating concerns into focused components.
 * Follows DRY by reusing specialized components.
 *
 * Parameters
 * ----------
 * props : ReaderControlsProps
 *     Component props including callbacks for progress control.
 */
export function ReaderControls({
  progress,
  onProgressChange,
  isProgressDisabled = false,
  isLoadingEpubData = false,
  pageColor = "light",
  pagingInfo,
  className,
}: ReaderControlsProps) {
  return (
    <div
      className={cn("flex flex-col gap-2 p-4", className)}
      style={{ backgroundColor: getControlBackgroundColor(pageColor) }}
    >
      <div className="flex items-center justify-center">
        <ProgressBar
          progress={progress}
          totalPages={pagingInfo?.totalPages}
          onProgressChange={onProgressChange}
          isDisabled={isProgressDisabled}
          isLoadingEpubData={isLoadingEpubData}
        />
      </div>

      <PagingInfoDisplay pagingInfo={pagingInfo} />
    </div>
  );
}
