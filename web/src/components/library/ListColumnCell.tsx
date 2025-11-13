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

import { ColumnCellRenderer } from "@/components/library/cells/ColumnCellRenderer";
import { cn } from "@/libs/utils";
import type { Book } from "@/types/book";
import type { ListColumnDefinition } from "@/types/listColumns";
import { getColumnAlignClass, getColumnWidthStyles } from "@/utils/listColumns";

export interface ListColumnCellProps {
  /** Column definition. */
  column: ListColumnDefinition;
  /** Column ID. */
  columnId: string;
  /** Book data. */
  book: Book;
  /** Callback when rating changes (optional). */
  onRatingChange?: (bookId: number, rating: number | null) => void;
}

/**
 * Renders a single column cell in the list view.
 *
 * Handles column width constraints and alignment.
 * Follows SRP by handling only single column rendering.
 * Uses IOC via callback props.
 *
 * Parameters
 * ----------
 * props : ListColumnCellProps
 *     Component props including column definition, book, and callbacks.
 */
export function ListColumnCell({
  column,
  columnId,
  book,
  onRatingChange,
}: ListColumnCellProps) {
  const alignClass = getColumnAlignClass(column.align);
  const widthStyles = getColumnWidthStyles(column.minWidth);

  return (
    <div
      key={columnId}
      className="flex min-w-0 items-center self-center"
      style={widthStyles}
    >
      <div className={cn("flex min-w-0 flex-1", alignClass)}>
        <ColumnCellRenderer
          column={column}
          book={book}
          onRatingChange={onRatingChange}
        />
      </div>
    </div>
  );
}
