// Copyright (C) 2026 knguyen and others
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

import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { cn } from "@/libs/utils";
import type { BookMergeRecommendation } from "@/services/bookService";

type BookDetail = BookMergeRecommendation["books"][0];

interface BookCardProps {
  book: BookDetail;
  isRecommended: boolean;
  isSelected: boolean;
  onSelect: (id: number) => void;
}

export function BookCard({
  book,
  isRecommended,
  isSelected,
  onSelect,
}: BookCardProps) {
  return (
    <button
      type="button"
      className={cn(
        "flex w-full cursor-pointer items-center gap-4 rounded-md border-2 p-4 text-left transition-colors",
        isSelected
          ? "border-primary-a0 bg-primary-a0/10"
          : "border-surface-a20 hover:border-surface-a30 hover:bg-surface-a10",
      )}
      onClick={() => onSelect(book.id)}
    >
      <input
        type="radio"
        checked={isSelected}
        onChange={() => onSelect(book.id)}
        className="h-4 w-4 flex-shrink-0 cursor-pointer"
        readOnly
        tabIndex={-1}
        aria-hidden="true"
      />
      <div className="relative h-24 w-16 flex-shrink-0 overflow-hidden rounded-md shadow-sm">
        {book.has_cover ? (
          <ImageWithLoading
            src={`/api/books/${book.id}/cover`}
            alt={`Cover of ${book.title}`}
            width={64}
            height={96}
            className="h-full w-full object-cover"
            containerClassName="h-full w-full"
            unoptimized
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-surface-a20 text-center text-[10px]">
            No Cover
          </div>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <h3 className="m-0 font-medium text-[var(--color-text-a0)] text-base">
            {book.title}
          </h3>
          {isRecommended && (
            <span className="rounded-full bg-primary-a0/20 px-2 py-0.5 text-primary-a0 text-xs">
              Recommended
            </span>
          )}
        </div>
        <div className="mt-1 flex flex-col gap-1 text-sm text-text-a30">
          <span>{book.author || "Unknown Author"}</span>
          <div className="flex flex-wrap gap-3 text-xs">
            {book.year && <span>{book.year}</span>}
            {book.publisher && <span>{book.publisher}</span>}
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            {book.formats.map((f) => (
              <span
                key={f.format}
                className="rounded bg-surface-a20 px-1.5 py-0.5 font-medium text-text-a60 text-xs"
              >
                {f.format} ({(f.size / 1024 / 1024).toFixed(2)} MB)
              </span>
            ))}
          </div>
        </div>
      </div>
    </button>
  );
}
