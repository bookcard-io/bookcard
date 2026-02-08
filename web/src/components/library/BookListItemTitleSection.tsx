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

import { cn } from "@/libs/utils";
import type { Book } from "@/types/book";
import { formatAuthors, getBookListItemAriaLabel } from "@/utils/book";
import { createEnterSpaceHandler } from "@/utils/keyboard";

export interface BookListItemTitleSectionProps {
  /** Book data. */
  book: Book;
  /** Whether the book is selected. */
  selected: boolean;
  /** Callback when section is clicked. */
  onClick: () => void;
  /** Whether to display the library badge. */
  showLibraryBadge?: boolean;
}

/**
 * Renders the title and author section of a list item.
 *
 * Follows SRP by handling only title/author display.
 * Uses IOC via callback props.
 *
 * Parameters
 * ----------
 * props : BookListItemTitleSectionProps
 *     Component props including book, selection state, and click handler.
 */
export function BookListItemTitleSection({
  book,
  selected,
  onClick,
  showLibraryBadge = false,
}: BookListItemTitleSectionProps) {
  const authorsText = formatAuthors(book.authors);
  const handleKeyDown = createEnterSpaceHandler(onClick);

  return (
    <div className="flex min-w-0 flex-1 flex-col gap-1 self-center">
      <button
        type="button"
        className={cn(
          "flex min-w-0 flex-1 cursor-pointer items-start gap-2 text-left",
          "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
          "focus:not-focus-visible:outline-none focus:outline-none",
        )}
        onClick={onClick}
        onKeyDown={handleKeyDown}
        aria-label={getBookListItemAriaLabel(book, selected)}
      >
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <h3
            className="m-0 truncate font-medium text-sm text-text-a0 leading-normal"
            title={book.title}
          >
            {book.title}
          </h3>
          <p
            className="m-0 truncate text-text-a20 text-xs leading-normal"
            title={authorsText}
          >
            {authorsText}
          </p>
          {showLibraryBadge && book.library_name && (
            <span className="mt-0.5 inline-block max-w-fit truncate rounded-sm bg-surface-a20 px-1.5 py-0.5 text-[0.625rem] text-text-a30">
              {book.library_name}
            </span>
          )}
        </div>
      </button>
    </div>
  );
}
