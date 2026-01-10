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
import { useCallback, useMemo } from "react";
import { Button } from "@/components/forms/Button";
import { useReadingProgress } from "@/hooks/useReadingProgress";
import { useReadStatus } from "@/hooks/useReadStatus";
import { cn } from "@/libs/utils";
import type { Book } from "@/types/book";
import { getReadableFormatForReader } from "@/utils/bookFormats";
import { ReadingHistoryList } from "./ReadingHistoryList";
import { ReadingProgressBar } from "./ReadingProgressBar";

export interface BookReadingInfoProps {
  /** Book data. */
  book: Book;
  /** Preferred format for reading (defaults to first available format). */
  preferredFormat?: string;
  /** Optional className. */
  className?: string;
}

/**
 * Book reading information panel component.
 *
 * Displays current progress, read status, and reading history for a book.
 * Includes "Continue Reading" and "Mark as Read/Unread" buttons.
 * For use on book detail pages.
 * Follows SRP by focusing solely on reading information display.
 *
 * Parameters
 * ----------
 * props : BookReadingInfoProps
 *     Component props including book data.
 */
export function BookReadingInfo({
  book,
  preferredFormat,
  className,
}: BookReadingInfoProps) {
  const router = useRouter();

  // Determine format to use
  const format = useMemo(() => {
    return (
      getReadableFormatForReader(book.formats || [], preferredFormat) || ""
    );
  }, [preferredFormat, book.formats]);

  const {
    progress,
    isLoading: isProgressLoading,
    error: progressError,
  } = useReadingProgress({
    bookId: book.id,
    format,
    enabled: !!format,
  });

  const {
    status,
    isLoading: isStatusLoading,
    markAsRead,
    markAsUnread,
    isUpdating: isStatusUpdating,
  } = useReadStatus({
    bookId: book.id,
    enabled: true,
  });

  const handleContinueReading = useCallback(() => {
    router.push(`/reading/${book.id}/${format}`);
  }, [router, book.id, format]);

  const handleMarkAsRead = useCallback(async () => {
    await markAsRead();
  }, [markAsRead]);

  const handleMarkAsUnread = useCallback(async () => {
    await markAsUnread();
  }, [markAsUnread]);

  const hasProgress = progress !== null;
  const isRead = status?.status === "read";

  return (
    <div className={cn("flex flex-col gap-4", className)}>
      <div className="flex flex-col gap-3">
        <h3 className="font-semibold text-base text-text-a0">
          Reading Progress
        </h3>

        {isProgressLoading && (
          <div className="flex items-center justify-center p-4">
            <span className="text-sm text-text-a40">Loading progress...</span>
          </div>
        )}

        {progressError && (
          <div className="flex items-center justify-center p-4">
            <span className="text-danger-a10 text-sm">
              Error: {progressError}
            </span>
          </div>
        )}

        {!isProgressLoading && !progressError && hasProgress && (
          <ReadingProgressBar progress={progress} />
        )}

        {!isProgressLoading && !progressError && !hasProgress && (
          <div className="flex items-center justify-center p-4">
            <span className="text-sm text-text-a40">
              No reading progress yet.
            </span>
          </div>
        )}

        <div className="flex gap-2">
          {hasProgress && (
            <Button
              type="button"
              variant="primary"
              size="medium"
              onClick={handleContinueReading}
            >
              Continue Reading
            </Button>
          )}
          {!hasProgress && format && (
            <Button
              type="button"
              variant="primary"
              size="medium"
              onClick={handleContinueReading}
            >
              Start Reading
            </Button>
          )}
          {isStatusLoading ? (
            <Button type="button" variant="secondary" size="medium" disabled>
              Loading...
            </Button>
          ) : isRead ? (
            <Button
              type="button"
              variant="secondary"
              size="medium"
              onClick={handleMarkAsUnread}
              disabled={isStatusUpdating}
            >
              {isStatusUpdating ? "Updating..." : "Mark as Unread"}
            </Button>
          ) : (
            <Button
              type="button"
              variant="secondary"
              size="medium"
              onClick={handleMarkAsRead}
              disabled={isStatusUpdating}
            >
              {isStatusUpdating ? "Updating..." : "Mark as Read"}
            </Button>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <ReadingHistoryList bookId={book.id} limit={10} />
      </div>
    </div>
  );
}
