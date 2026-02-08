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

export interface BookCardMetadataProps {
  /** Book title. */
  title: string;
  /** Book authors. */
  authors: string[];
  /** Name of the library this book belongs to. */
  libraryName?: string | null;
  /** Whether to display the library badge. */
  showLibraryBadge?: boolean;
}

/**
 * Book card metadata component (title, authors, and optional library badge).
 *
 * Displays book title and author information with an optional library badge
 * shown when viewing books from multiple libraries.
 * Follows SRP by focusing solely on metadata display.
 */
export function BookCardMetadata({
  title,
  authors,
  libraryName,
  showLibraryBadge = false,
}: BookCardMetadataProps) {
  const authorsText =
    authors.length > 0 ? authors.join(", ") : "Unknown Author";

  return (
    <div className="flex h-full min-h-16 flex-col gap-1 bg-surface-a10 p-[0.75rem] md:h-auto md:min-h-16">
      <h3
        className="m-0 line-clamp-2 font-[500] text-[0.875rem] text-text-a0 leading-[1.3]"
        title={title}
      >
        {title}
      </h3>
      <p
        className="m-0 line-clamp-1 text-text-a20 text-xs leading-[1.3]"
        title={authorsText}
      >
        {authorsText}
      </p>
      {showLibraryBadge && libraryName && (
        <span className="mt-0.5 inline-block max-w-full truncate rounded-sm bg-surface-a20 px-1.5 py-0.5 text-[0.625rem] text-text-a30">
          {libraryName}
        </span>
      )}
    </div>
  );
}
