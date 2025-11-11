"use client";

import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import { cn } from "@/libs/utils";
import type { Book } from "@/types/book";

export interface BookCardProps {
  /** Book data to display. */
  book: Book;
  /** All books in the grid (needed for range selection). */
  allBooks: Book[];
  /** Callback fired when card is clicked. Reserved for future use. */
  onClick?: (book: Book) => void;
  /** Callback fired when edit button is clicked. */
  onEdit?: (bookId: number) => void;
}

/**
 * Book card component for displaying a single book in the grid.
 *
 * Displays book cover thumbnail, title, and author(s).
 * Clicking the card opens the book view modal.
 * Selection is only available via the checkbox overlay.
 * Special overlay buttons (checkbox, edit, menu) stop event propagation.
 * Follows SRP by focusing solely on book display.
 */
export function BookCard({
  book,
  allBooks,
  onClick: _onClick,
  onEdit,
}: BookCardProps) {
  const { isSelected, handleBookClick } = useSelectedBooks();
  const selected = isSelected(book.id);

  const handleClick = () => {
    // Open book view modal via callback
    // Special overlay buttons (checkbox, edit, menu) stop propagation
    if (_onClick) {
      _onClick(book);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    // Open book view modal on Enter or Space
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (_onClick) {
        _onClick(book);
      }
    }
  };

  const handleCheckboxClick = (e: React.MouseEvent<HTMLDivElement>) => {
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

  const handleEditClick = (e: React.MouseEvent<HTMLDivElement>) => {
    e.stopPropagation();
    if (onEdit) {
      onEdit(book.id);
    }
  };

  const authorsText =
    book.authors.length > 0 ? book.authors.join(", ") : "Unknown Author";

  return (
    <button
      type="button"
      className={cn(
        "group flex cursor-pointer flex-col overflow-hidden rounded",
        "w-full border-2 border-transparent bg-gradient-to-b from-surface-a0 to-surface-a10 p-0 text-left",
        "transition-[transform,box-shadow,border-color] duration-200 ease-out",
        "hover:-translate-y-0.5 hover:shadow-card-hover",
        "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
        "focus:not-focus-visible:outline-none focus:outline-none",
        selected && "border-primary-a0 shadow-primary-glow outline-none",
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-label={`${book.title} by ${authorsText}${selected ? " (selected)" : ""}. Click to view details.`}
      data-book-card
    >
      <div className="relative aspect-[2/3] w-full overflow-hidden">
        {book.thumbnail_url ? (
          <ImageWithLoading
            src={book.thumbnail_url}
            alt={`Cover for ${book.title}`}
            width={200}
            height={300}
            className="h-full w-full object-cover"
            containerClassName="w-full h-full"
            unoptimized
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-surface-a20 to-surface-a10">
            <span className="text-sm text-text-a40 uppercase tracking-[0.5px]">
              No Cover
            </span>
          </div>
        )}
        <div
          className={cn(
            "absolute inset-0 z-10 transition-[opacity,background-color] duration-200 ease-in-out",
            // Default state: hidden
            "pointer-events-none bg-black/50 opacity-0",
            // When selected: visible but transparent, hide edit/menu buttons
            selected && "bg-transparent opacity-100",
            selected &&
              "[&_.edit-button]:pointer-events-none [&_.edit-button]:opacity-0",
            selected &&
              "[&_.menu-button]:pointer-events-none [&_.menu-button]:opacity-0",
            // On hover: show overlay and all buttons (using parent button's group)
            "group-hover:bg-black/50 group-hover:opacity-100",
            "group-hover:[&_.edit-button]:pointer-events-auto group-hover:[&_.edit-button]:opacity-100",
            "group-hover:[&_.menu-button]:pointer-events-auto group-hover:[&_.menu-button]:opacity-100",
            "group-hover:[&_.checkbox]:pointer-events-auto",
          )}
        >
          {/* biome-ignore lint/a11y/useSemanticElements: Cannot use button inside button, using div with role="button" for accessibility */}
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
            onClick={handleCheckboxClick}
            role="button"
            tabIndex={0}
            aria-label={selected ? "Deselect book" : "Select book"}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleCheckboxClick(
                  e as unknown as React.MouseEvent<HTMLDivElement>,
                );
              }
            }}
          >
            {selected && <i className="pi pi-check" aria-hidden="true" />}
          </div>
          {/* biome-ignore lint/a11y/useSemanticElements: Cannot use button inside button, using div with role="button" for accessibility */}
          <div
            className={cn(
              "edit-button pointer-events-auto flex cursor-default items-center justify-center",
              "text-text-a0 transition-[background-color,transform,opacity] duration-200 ease-in-out",
              "focus:shadow-focus-ring focus:outline-none",
              "absolute bottom-3 left-3 h-10 w-10 rounded-full",
              "border-none bg-white/20 backdrop-blur-sm",
              "hover:scale-110 hover:bg-white/30",
              "active:scale-95",
              "[&_i]:block [&_i]:text-lg",
            )}
            onClick={handleEditClick}
            role="button"
            tabIndex={0}
            aria-label={`Edit ${book.title}`}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleEditClick(
                  e as unknown as React.MouseEvent<HTMLDivElement>,
                );
              }
            }}
          >
            <i className="pi pi-pencil" aria-hidden="true" />
          </div>
          {/* biome-ignore lint/a11y/useSemanticElements: Cannot use button inside button, using div with role="button" for accessibility */}
          <div
            className={cn(
              "menu-button pointer-events-auto flex cursor-default items-center justify-center",
              "text-text-a0 transition-[background-color,transform,opacity] duration-200 ease-in-out",
              "focus:shadow-focus-ring focus:outline-none",
              "absolute right-3 bottom-3 h-10 w-10 rounded-full",
              "border-none bg-white/20 backdrop-blur-sm",
              "hover:scale-110 hover:bg-white/30",
              "active:scale-95",
              "[&_i]:block [&_i]:text-lg",
            )}
            onClick={(e) => {
              e.stopPropagation();
            }}
            role="button"
            tabIndex={0}
            aria-label="Menu"
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
              }
            }}
          >
            <i className="pi pi-ellipsis-v" aria-hidden="true" />
          </div>
        </div>
      </div>
      <div className="flex min-h-16 flex-col gap-1 bg-surface-a10 p-[0.75rem]">
        <h3
          className="m-0 line-clamp-2 font-[500] text-[0.875rem] text-text-a0 leading-[1.3]"
          title={book.title}
        >
          {book.title}
        </h3>
        <p
          className="m-0 line-clamp-1 text-text-a20 text-xs leading-[1.3]"
          title={authorsText}
        >
          {authorsText}
        </p>
      </div>
    </button>
  );
}
