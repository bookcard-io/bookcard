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

import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import { cn } from "@/libs/utils";
import type { Book } from "@/types/book";
import { createEnterSpaceHandler } from "@/utils/keyboard";

export interface BookCardCheckboxProps {
  /** Book data. */
  book: Book;
  /** All books in the grid (needed for range selection). */
  allBooks: Book[];
  /** Whether the book is selected. */
  selected: boolean;
  /** Variant style: 'grid' for overlay on cover, 'mobile' for inline. */
  variant?: "grid" | "mobile";
}

/**
 * Checkbox overlay button for book card selection.
 *
 * Handles book selection/deselection via checkbox interaction.
 * Follows SRP by focusing solely on selection UI and behavior.
 * Uses IOC via context and props.
 */
export function BookCardCheckbox({
  book,
  allBooks,
  selected,
  variant = "grid",
}: BookCardCheckboxProps) {
  const { handleBookClick } = useSelectedBooks();

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation();
    // Only way to add/remove books from selection is via the checkbox.
    // Create a synthetic event with ctrlKey set to toggle behavior.
    const syntheticEvent = {
      ...e,
      ctrlKey: true,
      metaKey: false,
      shiftKey: false,
    } as React.MouseEvent;
    handleBookClick(book, allBooks, syntheticEvent);
  };

  const handleKeyDown = createEnterSpaceHandler(() => {
    handleClick({} as React.MouseEvent<HTMLDivElement>);
  });

  const isMobile = variant === "mobile";

  return (
    /* biome-ignore lint/a11y/useSemanticElements: Cannot use button inside button, using div with role="button" for accessibility */
    <div
      className={cn(
        "checkbox pointer-events-auto flex cursor-default items-center justify-center",
        "transition-[background-color,border-color] duration-200 ease-in-out",
        "focus:shadow-focus-ring focus:outline-none",
        "[&_i]:block [&_i]:text-sm",
        isMobile
          ? [
              "relative h-8 w-8 rounded border-2 bg-transparent p-0",
              "text-text-a0",
              selected
                ? "border-primary-a0 bg-primary-a0"
                : "border-surface-a20 hover:bg-surface-a20",
            ]
          : [
              "absolute top-3 left-3 h-6 w-6 rounded border-2 bg-transparent p-0",
              "text-[var(--color-white)]",
              selected
                ? "border-primary-a0 bg-primary-a0"
                : "border-[var(--color-white)] hover:bg-[rgba(144,170,249,0.2)]",
            ],
      )}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label={selected ? "Deselect book" : "Select book"}
      onKeyDown={handleKeyDown}
    >
      {selected && <i className="pi pi-check" aria-hidden="true" />}
    </div>
  );
}
