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

import type { Book } from "@/types/book";
import type { ListColumnDefinition, ListColumnId } from "@/types/listColumns";
import { ListColumnCell } from "./ListColumnCell";

export interface ListColumnsSectionProps {
  /** Visible column IDs. */
  visibleColumns: ListColumnId[];
  /** All column definitions. */
  allColumns: Record<string, ListColumnDefinition>;
  /** Book data. */
  book: Book;
  /** Callback when rating changes (optional). */
  onRatingChange?: (bookId: number, rating: number | null) => void;
}

/**
 * Renders all visible columns (excluding title and authors) for a list item.
 *
 * Follows SRP by handling only column rendering.
 * Uses IOC via callback props.
 *
 * Parameters
 * ----------
 * props : ListColumnsSectionProps
 *     Component props including columns, book, and callbacks.
 */
export function ListColumnsSection({
  visibleColumns,
  allColumns,
  book,
  onRatingChange,
}: ListColumnsSectionProps) {
  const otherColumns = visibleColumns.filter(
    (id) => id !== "title" && id !== "authors",
  );

  return (
    <>
      {otherColumns.map((columnId) => {
        const column = allColumns[columnId];
        if (!column) {
          return null;
        }

        return (
          <ListColumnCell
            key={columnId}
            column={column}
            columnId={columnId}
            book={book}
            onRatingChange={onRatingChange}
          />
        );
      })}
    </>
  );
}
