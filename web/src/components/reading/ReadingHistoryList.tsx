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

import { useReadingHistory } from "@/hooks/useReadingHistory";
import { cn } from "@/libs/utils";

export interface ReadingHistoryListProps {
  /** Book ID. */
  bookId: number;
  /** Maximum number of sessions to display (default: 50). */
  limit?: number;
  /** Optional className. */
  className?: string;
}

/**
 * Reading history list component.
 *
 * Displays a list of reading sessions for a book.
 * Shows date, duration, and progress change.
 * For use on book detail pages.
 * Follows SRP by focusing solely on history display.
 *
 * Parameters
 * ----------
 * props : ReadingHistoryListProps
 *     Component props including book ID.
 */
export function ReadingHistoryList({
  bookId,
  limit = 50,
  className,
}: ReadingHistoryListProps) {
  const { sessions, total, isLoading, error } = useReadingHistory({
    bookId,
    limit,
  });

  const formatDuration = (seconds: number | null): string => {
    if (seconds === null) {
      return "Ongoing";
    }
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    if (minutes > 0) {
      return `${minutes}m`;
    }
    // Show at least 1s for any duration > 0 but < 1 second
    return secs > 0 ? `${secs}s` : "1s";
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return "Today";
    }
    if (diffDays === 1) {
      return "Yesterday";
    }
    if (diffDays < 7) {
      return `${diffDays} days ago`;
    }
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const formatProgressChange = (start: number, end: number | null): string => {
    if (end === null) {
      return `${Math.round(start * 100)}% → ...`;
    }
    const startPercent = Math.round(start * 100);
    const endPercent = Math.round(end * 100);
    const change = endPercent - startPercent;
    if (change === 0) {
      return `${startPercent}%`;
    }
    return `${startPercent}% → ${endPercent}% (+${change}%)`;
  };

  if (isLoading) {
    return (
      <div className={cn("flex items-center justify-center p-4", className)}>
        <span className="text-sm text-text-a40">
          Loading reading history...
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("flex items-center justify-center p-4", className)}>
        <span className="text-danger-a10 text-sm">Error: {error}</span>
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className={cn("flex items-center justify-center p-4", className)}>
        <span className="text-sm text-text-a40">No reading history yet.</span>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <div className="mb-2 flex items-center justify-between">
        <h3 className="font-semibold text-sm text-text-a0">Reading History</h3>
        <span className="text-text-a40 text-xs">{total} sessions</span>
      </div>
      <div className="flex flex-col gap-2">
        {sessions.map((session) => (
          <div
            key={session.id}
            className="flex items-center justify-between rounded-md border border-surface-a20 bg-surface-tonal-a0 p-3"
          >
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm text-text-a0">
                  {formatDate(session.started_at)}
                </span>
                <span className="text-text-a40 text-xs">
                  {formatDuration(session.duration ?? null)}
                </span>
              </div>
              <div className="flex items-center gap-2 text-text-a40 text-xs">
                <span>
                  Progress:{" "}
                  {formatProgressChange(
                    session.progress_start,
                    session.progress_end ?? null,
                  )}
                </span>
                {session.device && <span>• Device: {session.device}</span>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
