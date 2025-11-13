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

import { Button } from "@/components/forms/Button";
import type { Book } from "@/types/book";
import { formatFileSize } from "@/utils/format";

export interface BookFormatsSectionProps {
  /** Book data containing formats. */
  book: Book;
}

/**
 * Book formats section component.
 *
 * Displays book file formats and format actions.
 * Follows SRP by focusing solely on formats presentation.
 *
 * Parameters
 * ----------
 * props : BookFormatsSectionProps
 *     Component props including book data.
 */
export function BookFormatsSection({ book }: BookFormatsSectionProps) {
  return (
    <div className="mt-6 flex flex-col gap-4">
      <h3 className="m-0 font-bold text-text-a0 text-xl">Formats</h3>
      {book.formats && book.formats.length > 0 ? (
        <div className="flex flex-col gap-2">
          {book.formats.map((file) => (
            <div
              key={`${file.format}-${file.size}`}
              className="flex items-center justify-between gap-3 rounded-md border border-primary-a20 bg-surface-tonal-a10 p-3"
            >
              <div className="flex h-10 w-10 min-w-10 items-center justify-center rounded-lg border border-primary-a20 bg-surface-a20 font-semibold text-text-a0 text-xs">
                {file.format.toUpperCase()}
              </div>
              <div className="flex min-w-0 flex-1 flex-col gap-1">
                <span className="font-semibold text-sm text-text-a0">
                  {file.format.toUpperCase()}
                </span>
                <span className="text-sm text-text-a30">
                  {formatFileSize(file.size)}
                </span>
              </div>
              <div className="flex gap-1">
                <button
                  type="button"
                  className="flex flex-shrink-0 items-center justify-center rounded bg-transparent p-1.5 text-text-a30 transition-[transform,color,background-color] duration-200 hover:bg-surface-a20 hover:text-primary-a0 focus:outline focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2 active:scale-95"
                  aria-label={`Info for ${file.format.toUpperCase()}`}
                  title={`Info for ${file.format.toUpperCase()}`}
                >
                  <span className="pi pi-info-circle" aria-hidden="true" />
                </button>
                <button
                  type="button"
                  className="flex flex-shrink-0 items-center justify-center rounded bg-transparent p-1.5 text-text-a30 transition-[transform,color,background-color] duration-200 hover:bg-surface-a20 hover:text-primary-a0 focus:outline focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2 active:scale-95"
                  aria-label={`Copy ${file.format.toUpperCase()}`}
                  title={`Copy ${file.format.toUpperCase()}`}
                >
                  <span className="pi pi-copy" aria-hidden="true" />
                </button>
                <button
                  type="button"
                  className="flex flex-shrink-0 items-center justify-center rounded bg-transparent p-1.5 text-text-a30 transition-[transform,color,background-color] duration-200 hover:bg-surface-a20 hover:text-primary-a0 focus:outline focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2 active:scale-95"
                  aria-label={`Delete ${file.format.toUpperCase()}`}
                  title={`Delete ${file.format.toUpperCase()}`}
                >
                  <span className="pi pi-trash" aria-hidden="true" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-2 text-sm text-text-a30">No formats available</div>
      )}
      <div className="flex flex-col gap-2">
        <Button
          type="button"
          variant="ghost"
          size="small"
          className="!border-primary-a20 !text-primary-a20 hover:!text-primary-a20 w-full justify-start rounded-lg hover:border-primary-a10 hover:bg-surface-a20 focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2"
        >
          <span
            className="pi pi-plus mr-2 text-primary-a20"
            aria-hidden="true"
          />
          Add new format
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="small"
          className="!border-primary-a20 !text-primary-a20 hover:!text-primary-a20 w-full justify-start rounded-lg hover:border-primary-a10 hover:bg-surface-a20 focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2"
        >
          <span
            className="pi pi-arrow-right-arrow-left mr-2 text-primary-a20"
            aria-hidden="true"
          />
          Convert
        </Button>
      </div>
    </div>
  );
}
