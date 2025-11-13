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

import { DeleteBookConfirmationModal } from "@/components/books/DeleteBookConfirmationModal";
import { BookCardCover } from "@/components/library/BookCardCover";
import { BookCardEditButton } from "@/components/library/BookCardEditButton";
import { BookCardMenu } from "@/components/library/BookCardMenu";
import { BookCardMenuButton } from "@/components/library/BookCardMenuButton";
import { ListCheckbox } from "@/components/library/ListCheckbox";
import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import { useBookCardMenu } from "@/hooks/useBookCardMenu";
import { useBookCardMenuActions } from "@/hooks/useBookCardMenuActions";
import { useListColumns } from "@/hooks/useListColumns";
import { cn } from "@/libs/utils";
import type { Book } from "@/types/book";
import { formatDate } from "@/utils/format";
import { createEnterSpaceHandler } from "@/utils/keyboard";

export interface BookListItemProps {
  /** Book data to display. */
  book: Book;
  /** All books in the list (needed for range selection). */
  allBooks: Book[];
  /** Callback fired when item is clicked. */
  onClick?: (book: Book) => void;
  /** Callback fired when edit button is clicked. */
  onEdit?: (bookId: number) => void;
  /** Callback fired when book is deleted. */
  onBookDeleted?: (bookId: number) => void;
}

/**
 * Book list item component for displaying a single book in the list view.
 *
 * Orchestrates book list item display by composing specialized components.
 * Follows SRP by delegating to specialized components and hooks.
 * Uses IOC via hooks and component composition.
 * Follows SOC by separating concerns into independent components.
 * Follows DRY by reusing extracted components and utilities.
 */
export function BookListItem({
  book,
  allBooks,
  onClick: _onClick,
  onEdit,
  onBookDeleted,
}: BookListItemProps) {
  const { isSelected } = useSelectedBooks();
  const selected = isSelected(book.id);
  const menu = useBookCardMenu();
  const menuActions = useBookCardMenuActions({
    book,
    onBookClick: _onClick,
    onBookDeleted: () => onBookDeleted?.(book.id),
  });
  const { visibleColumns, allColumns } = useListColumns();

  const handleClick = () => {
    // Open book view modal via callback
    // Special overlay buttons (checkbox, edit, menu) stop propagation
    if (_onClick) {
      _onClick(book);
    }
  };

  const handleKeyDown = createEnterSpaceHandler(handleClick);

  const authorsText =
    book.authors.length > 0 ? book.authors.join(", ") : "Unknown Author";

  // Render cell content for a column
  const renderCell = (columnId: string) => {
    const column = allColumns[columnId as keyof typeof allColumns];
    if (!column) {
      return null;
    }

    const value = column.getValue(book);
    if (value === null) {
      return <span className="text-text-a40">—</span>;
    }

    // Special rendering for rating
    if (columnId === "rating") {
      if (book.rating === null || book.rating === undefined) {
        return <span className="text-text-a40">—</span>;
      }
      const rating = book.rating;
      return (
        <div className="flex items-center gap-1">
          <div className="flex">
            {Array.from({ length: 5 }, (_, i) => i).map((starIndex) => (
              <i
                key={`star-${starIndex}`}
                className={`pi ${
                  starIndex < rating ? "pi-star-fill" : "pi-star"
                } text-warning-a0 text-xs`}
                aria-hidden="true"
              />
            ))}
          </div>
        </div>
      );
    }

    // Format dates
    if (columnId === "pubdate" || columnId === "timestamp") {
      return <span>{formatDate(value)}</span>;
    }

    return (
      <span className="truncate" title={value}>
        {value}
      </span>
    );
  };

  return (
    <>
      <div
        className={cn(
          "group relative flex items-center gap-4 border-surface-a20 border-b py-2",
          "transition-[background-color] duration-200",
          "hover:bg-surface-a10",
          selected && "bg-surface-a10",
        )}
        data-book-card
      >
        {/* Checkbox column */}
        <div className="flex w-8 flex-shrink-0 items-center justify-center">
          <ListCheckbox book={book} allBooks={allBooks} selected={selected} />
        </div>

        {/* Cover art */}
        <div className="relative flex-shrink-0">
          <div className="relative w-8">
            <BookCardCover
              title={book.title}
              thumbnailUrl={book.thumbnail_url}
            />
          </div>
        </div>

        {/* Title and Author (always visible) */}
        <div className="flex min-w-0 flex-1 flex-col gap-1 self-center">
          <button
            type="button"
            className={cn(
              "flex min-w-0 flex-1 items-start gap-2 text-left",
              "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
              "focus:not-focus-visible:outline-none focus:outline-none",
            )}
            onClick={handleClick}
            onKeyDown={handleKeyDown}
            aria-label={`${book.title} by ${authorsText}${selected ? " (selected)" : ""}. Click to view details.`}
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
            </div>
          </button>
        </div>

        {/* Other columns */}
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
                  // Lock column width so rows align regardless of content length
                  width: column.minWidth,
                  minWidth: column.minWidth,
                  maxWidth: column.minWidth,
                  flexGrow: 0,
                  flexShrink: 0,
                  flexBasis: column.minWidth,
                }}
              >
                <div className={cn("flex min-w-0 flex-1", alignClass)}>
                  {renderCell(columnId)}
                </div>
              </div>
            );
          })}

        {/* Action buttons */}
        <div className="relative flex w-[72px] flex-shrink-0 items-center gap-2">
          {onEdit && (
            <BookCardEditButton
              bookTitle={book.title}
              onEdit={() => onEdit(book.id)}
              variant="list"
            />
          )}
          <BookCardMenuButton
            buttonRef={menu.menuButtonRef}
            isMenuOpen={menu.isMenuOpen}
            onToggle={menu.handleMenuToggle}
            variant="list"
          />
        </div>
      </div>
      <BookCardMenu
        isOpen={menu.isMenuOpen}
        onClose={menu.handleMenuClose}
        buttonRef={menu.menuButtonRef}
        cursorPosition={menu.cursorPosition}
        onBookInfo={menuActions.handleBookInfo}
        onSend={menuActions.handleSend}
        onMoveToLibrary={menuActions.handleMoveToLibrary}
        onMoveToShelf={menuActions.handleMoveToShelf}
        onConvert={menuActions.handleConvert}
        onDelete={menuActions.handleDelete}
        onMore={menuActions.handleMore}
      />
      <DeleteBookConfirmationModal
        isOpen={menuActions.deleteConfirmation.isOpen}
        dontShowAgain={menuActions.deleteConfirmation.dontShowAgain}
        deleteFilesFromDrive={
          menuActions.deleteConfirmation.deleteFilesFromDrive
        }
        onClose={menuActions.deleteConfirmation.close}
        onToggleDontShowAgain={
          menuActions.deleteConfirmation.toggleDontShowAgain
        }
        onToggleDeleteFilesFromDrive={
          menuActions.deleteConfirmation.toggleDeleteFilesFromDrive
        }
        onConfirm={menuActions.deleteConfirmation.confirm}
        bookTitle={book.title}
        isDeleting={menuActions.deleteConfirmation.isDeleting}
        error={menuActions.deleteConfirmation.error}
      />
    </>
  );
}
