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

  return (
    /* biome-ignore lint/a11y/useSemanticElements: Cannot use button inside button, using div with role="button" for accessibility */
    <div
      className={cn(
        "checkbox pointer-events-auto absolute top-3 left-3 flex cursor-default items-center justify-center",
        "text-text-a0 transition-[background-color,border-color] duration-200 ease-in-out",
        "h-6 w-6 rounded border-2 bg-transparent p-0",
        "focus:shadow-focus-ring focus:outline-none",
        selected
          ? "border-primary-a0 bg-primary-a0"
          : "border-text-a0 hover:bg-[rgba(144,170,249,0.2)]",
        "[&_i]:block [&_i]:text-sm",
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
