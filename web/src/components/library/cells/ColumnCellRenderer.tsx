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
import { DateCell } from "./DateCell";
import { RatingCell } from "./RatingCell";
import { TextCell } from "./TextCell";

export interface ColumnCellRendererProps {
  /** Column definition. */
  column: ListColumnDefinition;
  /** Book data. */
  book: Book;
  /** Callback when rating changes (optional, for rating column). */
  onRatingChange?: (bookId: number, rating: number | null) => void;
}

/**
 * Column cell renderer factory component.
 *
 * Routes to appropriate cell renderer based on column type.
 * Follows SRP by handling only routing logic.
 * Follows SOC by separating rendering concerns into specialized components.
 * Follows IOC by accepting renderers via composition.
 * Follows Open/Closed principle - can extend with new column types without modification.
 *
 * Parameters
 * ----------
 * props : ColumnCellRendererProps
 *     Component props including column definition, book, and optional callbacks.
 */
export function ColumnCellRenderer({
  column,
  book,
  onRatingChange,
}: ColumnCellRendererProps) {
  const value = column.getValue(book);

  // Route to specialized renderer based on column type
  const columnId = column.id as ListColumnId;

  // Rating column - use specialized rating renderer
  if (columnId === "rating") {
    return <RatingCell book={book} onRatingChange={onRatingChange} />;
  }

  // Date columns - use specialized date renderer
  if (columnId === "pubdate" || columnId === "timestamp") {
    return <DateCell value={value} />;
  }

  // Default - use text renderer for all other columns
  return <TextCell value={value} />;
}
