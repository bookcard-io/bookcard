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

import { useCallback } from "react";
import { formatFileSize } from "@/utils/format";

export interface BookFormat {
  /** File format (e.g., 'EPUB', 'PDF'). */
  format: string;
  /** File size in bytes. */
  size: number;
}

export interface BookViewFormatsProps {
  /** List of file formats. */
  formats: BookFormat[];
  /** Book ID for download. */
  bookId: number;
}

/**
 * Book view formats component.
 *
 * Displays available file formats with their sizes and download buttons.
 * Follows SRP by focusing solely on formats presentation.
 */
export function BookViewFormats({ formats, bookId }: BookViewFormatsProps) {
  const handleDownload = useCallback(
    async (format: string) => {
      try {
        const downloadUrl = `/api/books/${bookId}/download/${format}`;
        const response = await fetch(downloadUrl, {
          method: "GET",
        });
        if (!response.ok) {
          // eslint-disable-next-line no-console
          console.error("Download failed", await response.text());
          return;
        }
        const blob = await response.blob();
        const contentDisposition = response.headers.get("content-disposition");
        let filename = `book_${bookId}.${format.toLowerCase()}`;
        if (contentDisposition) {
          const match = contentDisposition.match(
            /filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i,
          );
          const cdName = decodeURIComponent(match?.[1] || match?.[2] || "");
          if (cdName) {
            filename = cdName;
          }
        }
        const objectUrl = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = objectUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(objectUrl);
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error("Download error", err);
      }
    },
    [bookId],
  );

  if (formats.length === 0) {
    return null;
  }

  return (
    <section className="flex flex-col gap-3">
      <h3 className="m-0 border-[var(--color-surface-a20)] border-b pb-1.5 font-semibold text-[var(--color-text-a0)] text-base">
        Available Formats
      </h3>
      <div className="mt-1 flex flex-col gap-2">
        {formats.map((file) => (
          <div
            key={`${file.format}-${file.size}`}
            className="flex items-center justify-between gap-3 rounded-md border border-[var(--color-surface-a20)] bg-[var(--color-surface-tonal-a10)] px-3 py-2"
          >
            <div className="flex min-w-0 flex-1 flex-col gap-1">
              <span className="font-semibold text-[var(--color-text-a0)] text-sm">
                {file.format.toUpperCase()}
              </span>
              <span className="text-[var(--color-text-a30)] text-sm">
                {formatFileSize(file.size)}
              </span>
            </div>
            <button
              type="button"
              onClick={() => handleDownload(file.format)}
              className="flex flex-shrink-0 items-center justify-center rounded border-none bg-transparent p-2 text-[var(--color-text-a30)] transition-all duration-200 hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-primary-a0)] focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2 active:scale-95"
              aria-label={`Download ${file.format.toUpperCase()} format`}
              title={`Download ${file.format.toUpperCase()}`}
            >
              <i className="pi pi-download text-base" aria-hidden="true" />
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
