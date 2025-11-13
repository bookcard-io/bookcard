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
import type { Book } from "@/types/book";

export interface BookCoverDisplayProps {
  /** Book data. */
  book: Book;
  /** Cover URL to display (staged or original). */
  coverUrl: string | null;
  /** Optional loading state (e.g., when backend is processing cover URL). */
  isLoading?: boolean;
}

/**
 * Book cover display component.
 *
 * Displays book cover image with overlay actions.
 * Follows SRP by focusing solely on cover display.
 *
 * Parameters
 * ----------
 * props : BookCoverDisplayProps
 *     Component props including book and cover URL.
 */
export function BookCoverDisplay({
  book,
  coverUrl,
  isLoading,
}: BookCoverDisplayProps) {
  const [isCoverOpen, setIsCoverOpen] = useState(false);
  const openCover = useCallback(() => setIsCoverOpen(true), []);
  const closeCover = useCallback(() => setIsCoverOpen(false), []);

  return (
    <>
      {coverUrl ? (
        <div className="relative aspect-[2/3] w-full overflow-hidden rounded-lg bg-surface-a20">
          <ImageWithLoading
            src={coverUrl}
            alt={`Cover for ${book.title}`}
            width={200}
            height={300}
            className="h-full w-full object-cover"
            isLoading={isLoading}
            unoptimized
          />
          <div className="absolute right-3 bottom-3 z-10 flex gap-2">
            <button
              type="button"
              className="hover:-translate-y-0.5 flex h-12 w-12 min-w-[3rem] items-center justify-center rounded-xl border-none bg-primary-a20 p-0 text-sm text-surface-a10 shadow-[0_2px_8px_rgba(0,0,0,0.15)] transition-all duration-200 ease-linear hover:bg-primary-a10 hover:shadow-[0_4px_12px_rgba(0,0,0,0.2)] focus:outline focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2 active:translate-y-0 active:bg-primary-a0 active:shadow-[0_2px_6px_rgba(0,0,0,0.15)] disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="View cover"
              title="View cover"
              onClick={openCover}
            >
              <span
                className="pi pi-arrow-up-right-and-arrow-down-left-from-center"
                aria-hidden="true"
              />
            </button>
            <button
              type="button"
              className="hover:-translate-y-0.5 flex h-12 w-12 min-w-[3rem] items-center justify-center rounded-xl border-none bg-primary-a20 p-0 text-sm text-surface-a10 shadow-[0_2px_8px_rgba(0,0,0,0.15)] transition-all duration-200 ease-linear hover:bg-primary-a10 hover:shadow-[0_4px_12px_rgba(0,0,0,0.2)] focus:outline focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2 active:translate-y-0 active:bg-primary-a0 active:shadow-[0_2px_6px_rgba(0,0,0,0.15)] disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Delete cover"
              title="Delete cover"
            >
              <span className="pi pi-trash" aria-hidden="true" />
            </button>
          </div>
        </div>
      ) : (
        <div
          className="flex aspect-[2/3] w-full items-center justify-center rounded-lg text-sm text-text-a40"
          style={{
            background:
              "linear-gradient(135deg, var(--color-surface-a20) 0%, var(--color-surface-a10) 100%)",
          }}
        >
          <span>No Cover</span>
        </div>
      )}
      <FullscreenImageModal
        src={coverUrl || ""}
        alt={`Cover for ${book.title}`}
        isOpen={isCoverOpen}
        onClose={closeCover}
      />
    </>
  );
}
