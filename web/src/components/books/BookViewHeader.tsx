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

import { useCallback, useState } from "react";
import { FullscreenImageModal } from "@/components/common/FullscreenImageModal";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { RatingDisplay } from "@/components/forms/RatingDisplay";
import { sendBookToDevice } from "@/services/bookService";
import type { Book } from "@/types/book";

export interface BookViewHeaderProps {
  /** Book data to display. */
  book: Book;
  /** Whether to show description. */
  showDescription?: boolean;
  /** Callback when edit icon is clicked. */
  onEdit?: () => void;
}

/**
 * Book view header component.
 *
 * Displays book cover, title, authors, series, and optionally description.
 * Follows SRP by focusing solely on header presentation.
 */
export function BookViewHeader({
  book,
  showDescription = false,
  onEdit,
}: BookViewHeaderProps) {
  const [isCoverOpen, setIsCoverOpen] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const openCover = useCallback(() => setIsCoverOpen(true), []);
  const closeCover = useCallback(() => setIsCoverOpen(false), []);

  const handleSend = useCallback(async () => {
    try {
      setIsSending(true);
      await sendBookToDevice(book.id);
      // Optionally show success message
    } catch (error) {
      console.error("Failed to send book:", error);
      // Optionally show error message
      alert(error instanceof Error ? error.message : "Failed to send book");
    } finally {
      setIsSending(false);
    }
  }, [book.id]);

  return (
    <div className="flex flex-col items-center gap-4 border-[var(--color-surface-a20)] border-b pb-4 text-center md:flex-row md:items-start md:gap-6 md:pb-6 md:text-left">
      {book.thumbnail_url && (
        <div className="flex flex-shrink-0 flex-col items-center">
          <div className="group relative inline-block leading-none">
            <ImageWithLoading
              src={book.thumbnail_url}
              alt={`Cover for ${book.title}`}
              width={200}
              height={300}
              className="rounded-md object-cover shadow-[0_4px_12px_rgba(0,0,0,0.3)]"
              containerClassName="inline-block"
              unoptimized
            />
            <button
              type="button"
              className="pointer-events-none absolute inset-0 flex cursor-default items-center justify-center rounded-md bg-[radial-gradient(circle_at_center,rgba(0,0,0,0.25)_0%,rgba(0,0,0,0.35)_60%,rgba(0,0,0,0.45)_100%)] opacity-0 transition-opacity duration-200 ease-linear hover:bg-[radial-gradient(circle_at_center,rgba(0,0,0,0.3)_0%,rgba(0,0,0,0.45)_60%,rgba(0,0,0,0.55)_100%)] focus-visible:outline-2 focus-visible:outline-[var(--color-primary-a0)] focus-visible:outline-offset-2 group-hover:pointer-events-auto group-hover:opacity-100"
              aria-label="View cover full screen"
              title="View cover"
              onClick={openCover}
            >
              <i
                className="pi pi-arrow-up-right-and-arrow-down-left-from-center text-[1.5rem] text-[var(--color-text-a0)] opacity-95 transition-transform duration-100 ease-linear hover:scale-110"
                aria-hidden="true"
              />
            </button>
          </div>
          <div className="mt-4 flex w-full items-center justify-center gap-4">
            <button
              type="button"
              className="group flex min-h-8 min-w-8 items-center justify-center rounded-full p-2 transition hover:scale-110 hover:bg-white/20 hover:backdrop-blur-sm focus-visible:outline-2 focus-visible:outline-[var(--color-primary-a0)] focus-visible:outline-offset-2 active:scale-95"
              aria-label="Read book"
              title="Read book"
            >
              <i
                className="pi pi-book text-[1.25rem] text-[var(--color-text-a30)] transition-colors group-hover:text-[var(--color-text-a0)]"
                aria-hidden="true"
              />
            </button>
            <button
              type="button"
              onClick={handleSend}
              disabled={isSending}
              className="group flex min-h-8 min-w-8 items-center justify-center rounded-full p-2 transition hover:scale-110 hover:bg-white/20 hover:backdrop-blur-sm focus-visible:outline-2 focus-visible:outline-[var(--color-primary-a0)] focus-visible:outline-offset-2 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Send book"
              title={isSending ? "Sending..." : "Send book"}
            >
              <i
                className={`pi ${isSending ? "pi-spin pi-spinner" : "pi-send"} text-[1.25rem] text-[var(--color-text-a30)] transition-colors group-hover:text-[var(--color-text-a0)]`}
                aria-hidden="true"
              />
            </button>
            <button
              type="button"
              className="group flex min-h-8 min-w-8 items-center justify-center rounded-full p-2 transition hover:scale-110 hover:bg-white/20 hover:backdrop-blur-sm focus-visible:outline-2 focus-visible:outline-[var(--color-primary-a0)] focus-visible:outline-offset-2 active:scale-95"
              aria-label="Convert format"
              title="Convert format"
            >
              <i
                className="pi pi-arrow-right-arrow-left text-[1.25rem] text-[var(--color-text-a30)] transition-colors group-hover:text-[var(--color-text-a0)]"
                aria-hidden="true"
              />
            </button>
            {onEdit && (
              <button
                type="button"
                onClick={onEdit}
                className="group flex min-h-8 min-w-8 items-center justify-center rounded-full p-2 transition hover:scale-110 hover:bg-white/20 hover:backdrop-blur-sm focus-visible:outline-2 focus-visible:outline-[var(--color-primary-a0)] focus-visible:outline-offset-2 active:scale-95"
                aria-label="Edit metadata"
                title="Edit metadata"
              >
                <i
                  className="pi pi-pencil text-[1.25rem] text-[var(--color-text-a30)] transition-colors group-hover:text-[var(--color-text-a0)]"
                  aria-hidden="true"
                />
              </button>
            )}
          </div>
          <FullscreenImageModal
            src={book.thumbnail_url}
            alt={`Cover for ${book.title}`}
            isOpen={isCoverOpen}
            onClose={closeCover}
          />
        </div>
      )}
      <div className="flex min-w-0 flex-1 flex-col gap-3">
        <h1 className="font-bold text-2xl text-[var(--color-text-a0)] leading-snug md:text-3xl">
          {book.title}
        </h1>
        {book.authors && book.authors.length > 0 && (
          <div className="flex items-baseline gap-2 text-base">
            <span className="font-medium text-[var(--color-text-a30)]">By</span>
            <span className="text-[var(--color-text-a0)]">
              {book.authors.join(", ")}
            </span>
          </div>
        )}
        {book.series && (
          <div className="flex items-baseline gap-2 text-base">
            <span className="font-medium text-[var(--color-text-a30)]">
              Series:
            </span>
            <span className="text-[var(--color-text-a0)]">
              {book.series}
              {book.series_index !== null &&
                book.series_index !== undefined && (
                  <span className="text-[var(--color-text-a30)]">
                    {" "}
                    #{book.series_index}
                  </span>
                )}
            </span>
          </div>
        )}
        {book.rating !== null && book.rating !== undefined && (
          <div className="mt-1 flex items-center">
            <RatingDisplay value={book.rating} showText size="medium" />
          </div>
        )}
        {showDescription && book.description && (
          <div className="mt-1 flex flex-col gap-2">
            <h2 className="m-0 font-semibold text-[var(--color-text-a0)] text-base">
              Description
            </h2>
            <div
              className="scrollbar-custom max-h-[200px] overflow-y-auto pr-2 text-[var(--color-text-a20)] text-sm leading-relaxed"
              // biome-ignore lint/security/noDangerouslySetInnerHtml: Book descriptions from Calibre are trusted HTML content
              dangerouslySetInnerHTML={{ __html: book.description }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
