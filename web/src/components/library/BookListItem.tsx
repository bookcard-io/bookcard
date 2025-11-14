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
import { DeleteBookConfirmationModal } from "@/components/books/DeleteBookConfirmationModal";
import { BookCardCover } from "@/components/library/BookCardCover";
import { BookCardEditButton } from "@/components/library/BookCardEditButton";
import { BookCardMenu } from "@/components/library/BookCardMenu";
import { BookCardMenuButton } from "@/components/library/BookCardMenuButton";
import { ListCheckbox } from "@/components/library/ListCheckbox";
import { ShelfEditModal } from "@/components/shelves/ShelfEditModal";
import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import { useBookCardMenu } from "@/hooks/useBookCardMenu";
import { useBookCardMenuActions } from "@/hooks/useBookCardMenuActions";
import { useCreateShelfWithBook } from "@/hooks/useCreateShelfWithBook";
import { useListColumns } from "@/hooks/useListColumns";
import { cn } from "@/libs/utils";
import type { Book } from "@/types/book";
import { getBookListItemAriaLabel } from "@/utils/book";
import { createEnterSpaceHandler } from "@/utils/keyboard";
import { BookListItemTitleSection } from "./BookListItemTitleSection";
import { ListColumnsSection } from "./ListColumnsSection";

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
  /** Callback fired when rating changes. */
  onRatingChange?: (bookId: number, rating: number | null) => void;
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
  onRatingChange,
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

  const shelfCreation = useCreateShelfWithBook({
    bookId: book.id,
  });

  /**
   * Handle book list item click.
   */
  const handleClick = useCallback(() => {
    // Open book view modal via callback
    // Special overlay buttons (checkbox, edit, menu) stop propagation
    if (_onClick) {
      _onClick(book);
    }
  }, [_onClick, book]);

  const handleCoverKeyDown = createEnterSpaceHandler(handleClick);

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
          <button
            type="button"
            className={cn(
              "relative w-8 cursor-pointer",
              "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
              "focus:not-focus-visible:outline-none focus:outline-none",
            )}
            onClick={(e) => {
              e.stopPropagation();
              handleClick();
            }}
            onKeyDown={handleCoverKeyDown}
            aria-label={getBookListItemAriaLabel(book, selected)}
          >
            <BookCardCover
              title={book.title}
              thumbnailUrl={book.thumbnail_url}
            />
          </button>
        </div>

        {/* Title and Author (always visible) */}
        <BookListItemTitleSection
          book={book}
          selected={selected}
          onClick={handleClick}
        />

        {/* Other columns */}
        <ListColumnsSection
          visibleColumns={visibleColumns}
          allColumns={allColumns}
          book={book}
          onRatingChange={onRatingChange}
        />

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
        bookId={book.id}
        onBookInfo={menuActions.handleBookInfo}
        onSend={menuActions.handleSend}
        onMoveToLibrary={menuActions.handleMoveToLibrary}
        onConvert={menuActions.handleConvert}
        onDelete={menuActions.handleDelete}
        onMore={menuActions.handleMore}
        isSendDisabled={menuActions.isSendDisabled}
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
      {shelfCreation.showCreateModal && (
        <ShelfEditModal
          shelf={null}
          onClose={shelfCreation.closeCreateModal}
          onSave={shelfCreation.handleCreateShelf}
        />
      )}
    </>
  );
}
