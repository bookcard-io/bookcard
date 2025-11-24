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

import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { cn } from "@/libs/utils";
import type { ReadingProgress } from "@/types/reading";

export interface ReadingProgressBarProps {
  /** Reading progress data. */
  progress: ReadingProgress;
  /** Callback when progress bar is clicked (to jump to reading position). */
  onJumpToPosition?: () => void;
  /** Optional className. */
  className?: string;
}

/**
 * Reading progress bar component.
 *
 * Full-width progress bar for book detail pages.
 * Shows progress, format, last updated, and is clickable to jump to reading position.
 * Follows SRP by focusing solely on progress visualization.
 *
 * Parameters
 * ----------
 * props : ReadingProgressBarProps
 *     Component props including progress data.
 */
export function ReadingProgressBar({
  progress,
  onJumpToPosition,
  className,
}: ReadingProgressBarProps) {
  const router = useRouter();
  const percentage = Math.round(progress.progress * 100);
  const updatedAt = new Date(progress.updated_at);
  const formattedDate = updatedAt.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
  const formattedTime = updatedAt.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });

  const handleClick = useCallback(() => {
    if (onJumpToPosition) {
      onJumpToPosition();
    } else {
      // Default: navigate to reader page
      router.push(`/reading/${progress.book_id}/${progress.format}`);
    }
  }, [onJumpToPosition, router, progress.book_id, progress.format]);

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm text-text-a0">
            {percentage}% Complete
          </span>
          <span className="text-text-a40 text-xs">({progress.format})</span>
        </div>
        <span className="text-text-a40 text-xs">
          Last updated: {formattedDate} at {formattedTime}
        </span>
      </div>
      <button
        type="button"
        onClick={handleClick}
        className="group relative h-3 w-full overflow-hidden rounded-full bg-gray-200 transition-all hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600"
        aria-label={`Reading progress: ${percentage}%. Click to continue reading.`}
      >
        <div
          className="h-full bg-primary-a0 transition-all duration-300 ease-out group-hover:bg-primary-a10"
          style={{ width: `${percentage}%` }}
        />
      </button>
      {progress.cfi && (
        <span className="text-text-a40 text-xs">
          Position: {progress.cfi.substring(0, 50)}
          {progress.cfi.length > 50 ? "..." : ""}
        </span>
      )}
      {progress.page_number !== null && (
        <span className="text-text-a40 text-xs">
          Page: {progress.page_number}
        </span>
      )}
    </div>
  );
}
