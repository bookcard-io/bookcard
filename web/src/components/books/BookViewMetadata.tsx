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

import type { Book } from "@/types/book";
import { formatDate } from "@/utils/format";

export interface BookViewMetadataProps {
  /** Book data to display. */
  book: Book;
}

/**
 * Book view metadata component.
 *
 * Displays publication, classification, and identifier information.
 * Follows SRP by focusing solely on metadata presentation.
 */
export function BookViewMetadata({ book }: BookViewMetadataProps) {
  return (
    <div className="grid grid-cols-1 gap-5 md:grid-cols-[repeat(auto-fit,minmax(200px,1fr))]">
      {/* Publication Info */}
      <section className="flex flex-col gap-3">
        <h3 className="m-0 border-[var(--color-surface-a20)] border-b pb-1.5 font-semibold text-[var(--color-text-a0)] text-base">
          Publication
        </h3>
        <div className="flex flex-col gap-0.5">
          <span className="font-medium text-[var(--color-text-a30)] text-sm">
            Published:
          </span>
          <span className="text-[var(--color-text-a0)] text-base">
            {formatDate(book.pubdate)}
          </span>
        </div>
        {book.publisher && (
          <div className="flex flex-col gap-0.5">
            <span className="font-medium text-[var(--color-text-a30)] text-sm">
              Publisher:
            </span>
            <span className="text-[var(--color-text-a0)] text-base">
              {book.publisher}
            </span>
          </div>
        )}
        {book.languages && book.languages.length > 0 && (
          <div className="flex flex-col gap-0.5">
            <span className="font-medium text-[var(--color-text-a30)] text-sm">
              Languages:
            </span>
            <span className="text-[var(--color-text-a0)] text-base">
              {book.languages.map((lang) => lang.toUpperCase()).join(", ")}
            </span>
          </div>
        )}
      </section>

      {/* Classification */}
      <section className="flex flex-col gap-3">
        <h3 className="m-0 border-[var(--color-surface-a20)] border-b pb-1.5 font-semibold text-[var(--color-text-a0)] text-base">
          Classification
        </h3>
        {book.tags && book.tags.length > 0 && (
          <div className="flex flex-col gap-0.5">
            <span className="font-medium text-[var(--color-text-a30)] text-sm">
              Tags:
            </span>
            <div className="mt-1 flex flex-wrap gap-2">
              {book.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-block rounded-full border border-[var(--color-surface-a20)] bg-[var(--color-surface-tonal-a10)] px-3 py-1 text-[var(--color-text-a20)] text-sm"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Identifiers */}
      {book.identifiers && book.identifiers.length > 0 && (
        <section className="flex flex-col gap-3">
          <h3 className="m-0 border-[var(--color-surface-a20)] border-b pb-1.5 font-semibold text-[var(--color-text-a0)] text-base">
            Identifiers
          </h3>
          {book.identifiers.map((ident) => (
            <div
              key={`${ident.type}-${ident.val}`}
              className="flex flex-col gap-0.5"
            >
              <span className="font-medium text-[var(--color-text-a30)] text-sm">
                {ident.type.toUpperCase()}:
              </span>
              <span className="text-[var(--color-text-a0)] text-base">
                {ident.val}
              </span>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
