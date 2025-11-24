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

import { useMemo } from "react";
import { useReadingProgress } from "@/hooks/useReadingProgress";
import { useReadStatus } from "@/hooks/useReadStatus";
import { cn } from "@/libs/utils";
import type { Book } from "@/types/book";
import { ReadingProgressIndicator } from "./ReadingProgressIndicator";

export interface BookCardProgressProps {
  /** Book data. */
  book: Book;
  /** Preferred format for reading (defaults to first available format). */
  preferredFormat?: string;
  /** Optional className. */
  className?: string;
}

/**
 * Book card progress overlay component.
 *
 * Displays progress bar and read status badge on book cards.
 * For use in book grid and list views.
 * Follows SRP by focusing solely on progress overlay display.
 *
 * Parameters
 * ----------
 * props : BookCardProgressProps
 *     Component props including book data.
 */
export function BookCardProgress({
  book,
  preferredFormat,
  className,
}: BookCardProgressProps) {
  // Determine format to use
  const format = useMemo(() => {
    if (
      preferredFormat &&
      book.formats?.some((f) => f.format === preferredFormat)
    ) {
      return preferredFormat;
    }
    return book.formats?.[0]?.format || "EPUB";
  }, [preferredFormat, book.formats]);

  const { progress } = useReadingProgress({
    bookId: book.id,
    format,
    enabled: !!format,
  });

  const { status } = useReadStatus({
    bookId: book.id,
    enabled: true,
  });

  if (!progress) {
    return null;
  }

  return (
    <div
      className={cn(
        "absolute right-0 bottom-0 left-0 bg-gradient-to-t from-black/80 to-transparent p-2",
        className,
      )}
    >
      <ReadingProgressIndicator
        progress={progress.progress}
        readStatus={
          (status?.status as "not_read" | "reading" | "read" | undefined) ??
          null
        }
        showStatus={true}
        size="small"
      />
    </div>
  );
}
