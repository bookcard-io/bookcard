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
import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import { useListColumns } from "@/hooks/useListColumns";
import { cn } from "@/libs/utils";
import type { Book } from "@/types/book";
import { createEnterSpaceHandler } from "@/utils/keyboard";

export interface ListHeaderProps {
  /** All books in the list (for select all functionality). */
  allBooks: Book[];
}

/**
 * List header component for displaying column headers.
 *
 * Displays column labels aligned with the columns in BookListItem.
 * Includes select-all checkbox in the checkbox column.
 * Follows SRP by handling only header display.
 * Uses IOC via hooks for column configuration.
 */
export function ListHeader({ allBooks }: ListHeaderProps) {
  const { visibleColumns, allColumns } = useListColumns();
  const { selectedBookIds, selectAll, clearSelection } = useSelectedBooks();

  const allSelected =
    allBooks.length > 0 &&
    allBooks.every((book) => selectedBookIds.has(book.id));
  const someSelected = allBooks.some((book) => selectedBookIds.has(book.id));

  const handleSelectAll = useCallback(() => {
    if (allSelected) {
      clearSelection();
    } else {
      selectAll(allBooks);
    }
  }, [allSelected, allBooks, selectAll, clearSelection]);

  const handleKeyDown = createEnterSpaceHandler(handleSelectAll);

  return (
    <div
      className={cn(
        "sticky top-0 z-10 flex items-center gap-4 border-surface-a30 border-b-2 bg-surface-a0 py-2",
        "shadow-sm",
      )}
    >
      {/* Checkbox column header */}
      <div className="flex w-8 flex-shrink-0 items-center justify-center">
        {/* biome-ignore lint/a11y/useSemanticElements: Using div with role="button" for consistency with ListCheckbox */}
        <div
          className={cn(
            "checkbox flex cursor-default items-center justify-center",
            "text-text-a0 transition-[background-color,border-color] duration-200 ease-in-out",
            "h-6 w-6 rounded border-2 bg-transparent p-0",
            // "focus:shadow-focus-ring focus:outline-none",
            allSelected
              ? "border-primary-a0 bg-primary-a0"
              : someSelected
                ? "border-primary-a0 bg-primary-a0/50"
                : "border-surface-a30 hover:bg-surface-a10",
            "[&_i]:block [&_i]:text-sm",
          )}
          onClick={handleSelectAll}
          role="button"
          tabIndex={0}
          aria-label={allSelected ? "Deselect all books" : "Select all books"}
          onKeyDown={handleKeyDown}
        >
          {allSelected && <i className="pi pi-check" aria-hidden="true" />}
          {someSelected && !allSelected && (
            <i className="pi pi-minus" aria-hidden="true" />
          )}
        </div>
      </div>

      {/* Cover art column header (empty) */}
      <div className="flex-shrink-0">
        <div className="w-8" />
      </div>

      {/* Title and Author header */}
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <h3 className="m-0 font-semibold text-text-a30 text-xs uppercase tracking-wide">
          {allColumns.title.label}
        </h3>
        <p className="m-0 font-semibold text-text-a30 text-xs uppercase tracking-wide">
          {allColumns.authors.label}
        </p>
      </div>

      {/* Other column headers */}
      {visibleColumns
        .filter((id) => id !== "title" && id !== "authors")
        .map((columnId) => {
          const column = allColumns[columnId];
          if (!column) {
            return null;
          }

          const align = column.align ?? "center";
          const alignClass =
            align === "left"
              ? "justify-start text-left"
              : align === "right"
                ? "justify-end text-right"
                : "justify-center text-center";

          return (
            <div
              key={columnId}
              className="flex min-w-0 items-center self-center"
              style={{
                // Keep header cells aligned with row cells by locking width
                width: column.minWidth,
                minWidth: column.minWidth,
                maxWidth: column.minWidth,
                flexGrow: 0,
                flexShrink: 0,
                flexBasis: column.minWidth,
              }}
            >
              <div className={cn("flex min-w-0 flex-1", alignClass)}>
                <span className="font-semibold text-text-a30 text-xs uppercase tracking-wide">
                  {column.label}
                </span>
              </div>
            </div>
          );
        })}

      {/* Action buttons header (empty) */}
      <div className="relative flex w-[72px] flex-shrink-0 items-center gap-2">
        {/* reserved width to align with row action buttons */}
      </div>
    </div>
  );
}
