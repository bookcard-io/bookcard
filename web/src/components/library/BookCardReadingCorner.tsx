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

import type { MouseEvent } from "react";
import { useCallback, useMemo } from "react";
import { BsBookmarkFill } from "react-icons/bs";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import { useReadStatus } from "@/hooks/useReadStatus";
import { cn } from "@/libs/utils";
import type { BookReadingSummary } from "@/types/book";
import { isReadStatus, isUnreadStatus } from "@/utils/readingStatus";

export interface BookCardReadingCornerProps {
  /** Book ID. */
  bookId: number;
  /** Denormalized reading summary (status + max progress). */
  readingSummary?: BookReadingSummary | null;
  /** Optional class name for positioning/styling. */
  className?: string;
}

/**
 * Calculate reading progress percentage from max progress value.
 *
 * Parameters
 * ----------
 * maxProgress : number | null
 *     Maximum progress value (0.0 to 1.0).
 *
 * Returns
 * -------
 * number | null
 *     Percentage (0-100) or null if no valid progress.
 */
function calculatePercent(maxProgress: number | null): number | null {
  if (maxProgress === null) {
    return null;
  }
  const clamped = Math.max(0, Math.min(1, maxProgress));
  const rounded = Math.round(clamped * 100);
  return rounded > 0 ? rounded : null;
}

/**
 * Book card corner badge for read status and progress.
 *
 * Displays a "READ" ribbon when the book is marked as read. Otherwise, when
 * progress exists, shows the highest percent read over a bookmark icon.
 * For unread books, hovering over the corner control marks the book as read.
 *
 * Parameters
 * ----------
 * props : BookCardReadingCornerProps
 *     Book identifier and denormalized reading summary for display.
 */
export function BookCardReadingCorner({
  bookId,
  readingSummary,
  className,
}: BookCardReadingCornerProps) {
  const { activeLibrary, isLoading: isActiveLibraryLoading } =
    useActiveLibrary();
  const hasActiveLibrary = activeLibrary !== null && !isActiveLibraryLoading;

  // Single source of truth: useReadStatus writes to the shared react-query cache.
  // We keep `enabled: false` here to avoid fan-out fetching in grids; we still
  // receive cache updates triggered by other components (e.g., the modal).
  const { status, markAsRead, isUpdating } = useReadStatus({
    bookId,
    enabled: false,
  });

  // Determine effective status: read-status cache > reading summary.
  // `readingSummary` gives the initial denormalized state from list queries.
  const effectiveStatus = useMemo(() => {
    return status?.status ?? readingSummary?.read_status ?? null;
  }, [readingSummary?.read_status, status?.status]);

  const effectiveMaxProgress = readingSummary?.max_progress ?? null;

  // Memoize display state to avoid unnecessary recalculations
  const displayState = useMemo(() => {
    const isRead = isReadStatus(effectiveStatus);
    const isUnread = isUnreadStatus(effectiveStatus);
    const percent = calculatePercent(effectiveMaxProgress);
    const hasProgress = percent !== null && percent > 0;
    const shouldShow = hasProgress;

    return {
      isRead,
      isUnread,
      percent,
      hasProgress,
      shouldShow,
    };
  }, [effectiveStatus, effectiveMaxProgress]);

  const canUpdate = hasActiveLibrary && !isUpdating;

  const handleToggleReadStatus = useCallback(
    async (e: MouseEvent<HTMLButtonElement>) => {
      e.preventDefault();
      e.stopPropagation();

      if (!canUpdate) {
        return;
      }

      // Button is only rendered when unread, so we always mark as read
      await markAsRead();
    },
    [canUpdate, markAsRead],
  );

  if (!hasActiveLibrary) {
    return null;
  }

  if (displayState.isRead) {
    return (
      <div
        className={cn(
          "pointer-events-none absolute top-0 right-0 z-20 h-16 w-16 overflow-hidden",
          className,
        )}
        aria-hidden="true"
      >
        <div
          className={cn(
            "absolute top-[14px] right-[-36px] w-[120px] rotate-45",
            "bg-success-a0 px-2 py-1 text-center font-semibold text-[11px] text-[var(--color-white)] tracking-[0.08em] shadow-sm",
          )}
        >
          READ
        </div>
      </div>
    );
  }

  // Show bookmark with percent when there is progress but status is not READ.
  // Also render a clickable corner control for unread books to toggle read status.
  // Visibility: show on card hover OR when there is a non-zero reading percentage.
  return (
    <button
      type="button"
      className={cn(
        "absolute top-2 right-2 z-20 inline-flex h-9 w-9 items-center justify-center rounded-md",
        "text-text-a0 shadow-sm",
        "transition-all duration-150",
        // Default: hidden unless there's progress
        displayState.shouldShow ? "opacity-100" : "opacity-0",
        // Show on card hover
        "group-hover:opacity-100",
        displayState.isUnread &&
          "hover:bg-primary-a0 hover:text-[var(--color-white)]",
        isUpdating && "cursor-wait opacity-80",
        className,
      )}
      onClick={handleToggleReadStatus}
      aria-label={displayState.isUnread ? "Mark as read" : "Toggle read status"}
      title={
        displayState.isUnread
          ? displayState.percent !== null
            ? `Mark as read (${displayState.percent}%)`
            : "Mark as read"
          : "Toggle read status"
      }
    >
      <span className="relative inline-flex h-6 w-6 items-center justify-center">
        <BsBookmarkFill className="h-5 w-5" aria-hidden="true" />
        {displayState.percent !== null && (
          <span
            className={cn(
              "-translate-x-1/2 -translate-y-1/2 absolute top-1/2 left-1/2",
              "rounded px-1 font-semibold text-[10px] leading-none",
              "bg-surface-a0/70 text-text-a0 backdrop-blur",
            )}
          >
            {displayState.percent}%
          </span>
        )}
      </span>
    </button>
  );
}
