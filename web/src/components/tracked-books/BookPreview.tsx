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

import type { ReactNode } from "react";
import { FaBook } from "react-icons/fa";
import type { MetadataSearchResult } from "@/types/trackedBook";

export interface BookPreviewProps {
  book: MetadataSearchResult;
  children?: ReactNode;
}

export function BookPreview({ book, children }: BookPreviewProps) {
  // Determine display year (prioritize published_date year, fallback to year field, ensure no duplicates)
  const displayYear =
    book.published_date?.substring(0, 4) || book.year || undefined;

  return (
    <>
      {/* Poster */}
      <div className="flex-shrink-0 md:w-[160px]">
        <div className="aspect-[2/3] w-full overflow-hidden rounded-md bg-surface-tonal-a10 shadow-md">
          {book.cover_url ? (
            <img
              src={book.cover_url}
              alt={book.title}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center">
              <FaBook className="text-4xl text-text-a40" />
            </div>
          )}
        </div>
      </div>

      {/* Details & Form Container */}
      <div className="flex flex-1 flex-col gap-6">
        <div className="flex flex-col gap-2">
          <div className="flex flex-col gap-2 md:flex-row md:items-baseline md:justify-between">
            <h3 className="font-bold text-2xl text-text-a0">
              {book.title}
              {displayYear && (
                <span className="ml-2 font-normal text-lg text-text-a30">
                  ({displayYear})
                </span>
              )}
            </h3>
          </div>
          <div className="mt-1 text-text-a30">{book.author}</div>
          <p className="mt-4 line-clamp-3 text-sm text-text-a30">
            {book.description || "No description available."}
          </p>
        </div>
        {children}
      </div>
    </>
  );
}
