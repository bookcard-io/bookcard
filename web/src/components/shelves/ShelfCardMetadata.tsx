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

export interface ShelfCardMetadataProps {
  /** Shelf name. */
  name: string;
  /** Number of books in the shelf. */
  bookCount: number;
  /** Whether the shelf is public/shared. */
  isPublic: boolean;
}

/**
 * Shelf card metadata component (name and book count).
 *
 * Displays shelf name and book count information.
 * Shows globe icon when shelf is public.
 * Follows SRP by focusing solely on metadata display.
 * Follows DRY by reusing BookCardMetadata styling pattern.
 */
export function ShelfCardMetadata({
  name,
  bookCount,
  isPublic,
}: ShelfCardMetadataProps) {
  const bookCountText = bookCount === 1 ? "1 book" : `${bookCount} books`;

  return (
    <div className="relative flex min-h-16 flex-col gap-1 bg-surface-a10 p-[0.75rem]">
      {isPublic && (
        <div
          className="absolute inset-y-0 right-[0.75rem] flex items-center justify-center"
          title="Shelf is shared"
        >
          <i
            className="pi pi-globe text-base text-text-a30"
            aria-hidden="true"
          />
        </div>
      )}
      <h3
        className="m-0 line-clamp-2 font-[500] text-[0.875rem] text-text-a0 leading-[1.3]"
        title={name}
      >
        {name}
      </h3>
      <p
        className="m-0 line-clamp-1 text-text-a20 text-xs leading-[1.3]"
        title={bookCountText}
      >
        {bookCountText}
      </p>
    </div>
  );
}
