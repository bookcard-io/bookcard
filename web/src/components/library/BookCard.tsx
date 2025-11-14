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
import { BookCardCheckbox } from "@/components/library/BookCardCheckbox";
import { BookCardCover } from "@/components/library/BookCardCover";
import { BookCardEditButton } from "@/components/library/BookCardEditButton";
import { BookCardMenu } from "@/components/library/BookCardMenu";
import { BookCardMenuButton } from "@/components/library/BookCardMenuButton";
import { BookCardMetadata } from "@/components/library/BookCardMetadata";
import { BookCardOverlay } from "@/components/library/BookCardOverlay";
import { ShelfEditModal } from "@/components/shelves/ShelfEditModal";
import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import { useBookCardMenu } from "@/hooks/useBookCardMenu";
import { useBookCardMenuActions } from "@/hooks/useBookCardMenuActions";
import { useCreateShelfWithBook } from "@/hooks/useCreateShelfWithBook";
import { cn } from "@/libs/utils";
import type { Book } from "@/types/book";
import { getBookCardAriaLabel } from "@/utils/book";
import { createEnterSpaceHandler } from "@/utils/keyboard";

export interface BookCardProps {
  /** Book data to display. */
  book: Book;
  /** All books in the grid (needed for range selection). */
  allBooks: Book[];
  /** Callback fired when card is clicked. Reserved for future use. */
  onClick?: (book: Book) => void;
  /** Callback fired when edit button is clicked. */
  onEdit?: (bookId: number) => void;
  /** Callback fired when book is deleted. */
  onBookDeleted?: (bookId: number) => void;
}

/**
 * Book card component for displaying a single book in the grid.
 *
 * Orchestrates book card display by composing specialized components.
 * Follows SRP by delegating to specialized components and hooks.
 * Uses IOC via hooks and component composition.
 * Follows SOC by separating concerns into independent components.
 * Follows DRY by reusing extracted components and utilities.
 */
export function BookCard({
  book,
  allBooks,
  onClick: _onClick,
  onEdit,
  onBookDeleted,
}: BookCardProps) {
  const { isSelected } = useSelectedBooks();
  const selected = isSelected(book.id);
  const menu = useBookCardMenu();
  const menuActions = useBookCardMenuActions({
    book,
    onBookClick: _onClick,
    onBookDeleted: () => onBookDeleted?.(book.id),
  });

  const shelfCreation = useCreateShelfWithBook({
    bookId: book.id,
  });

  /**
   * Handle book card click.
   */
  const handleClick = useCallback(() => {
    // Open book view modal via callback
    // Special overlay buttons (checkbox, edit, menu) stop propagation
    if (_onClick) {
      _onClick(book);
    }
  }, [_onClick, book]);

  const handleKeyDown = createEnterSpaceHandler(handleClick);

  return (
    <>
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
        aria-label={getBookCardAriaLabel(book, selected)}
        data-book-card
      >
        <div className="relative">
          <BookCardCover title={book.title} thumbnailUrl={book.thumbnail_url} />
          <BookCardOverlay selected={selected}>
            <BookCardCheckbox
              book={book}
              allBooks={allBooks}
              selected={selected}
            />
            {onEdit && (
              <BookCardEditButton
                bookTitle={book.title}
                onEdit={() => onEdit(book.id)}
              />
            )}
            <BookCardMenuButton
              buttonRef={menu.menuButtonRef}
              isMenuOpen={menu.isMenuOpen}
              onToggle={menu.handleMenuToggle}
            />
          </BookCardOverlay>
        </div>
        <BookCardMetadata title={book.title} authors={book.authors} />
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
      </button>
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
