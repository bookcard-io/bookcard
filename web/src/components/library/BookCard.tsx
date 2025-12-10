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
import { BookCardActions } from "@/components/library/BookCardActions";
import { BookCardCenterActions } from "@/components/library/BookCardCenterActions";
import { BookCardCover } from "@/components/library/BookCardCover";
import {
  BookCardCompactLayout,
  BookCardDefaultLayout,
} from "@/components/library/BookCardLayouts";
import { BookCardMenu } from "@/components/library/BookCardMenu";
import { BookCardMetadata } from "@/components/library/BookCardMetadata";
import { BookCardModals } from "@/components/library/BookCardModals";
import { BookCardOverlay } from "@/components/library/BookCardOverlay";
import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import { useBookCardMenu } from "@/hooks/useBookCardMenu";
import { useBookCardMenuActions } from "@/hooks/useBookCardMenuActions";
import { useBookCardModals } from "@/hooks/useBookCardModals";
import { useBookNavigation } from "@/hooks/useBookNavigation";
import { useCreateShelfWithBook } from "@/hooks/useCreateShelfWithBook";
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
  /** Whether to show selection checkbox. Defaults to false. */
  showSelection?: boolean;
  /** Whether to hide all action buttons (checkbox, edit, menu). Defaults to false. */
  hideActions?: boolean;
  /** Layout variant. 'default' is responsive, 'compact' forces mobile-like layout. Defaults to 'default'. */
  variant?: "default" | "compact";
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
  showSelection = false,
  hideActions = false,
  variant = "default",
}: BookCardProps) {
  const { isSelected } = useSelectedBooks();
  const selected = isSelected(book.id);
  const showActions = !hideActions;

  // Hooks for logic and state
  const menu = useBookCardMenu();
  const menuActions = useBookCardMenuActions({
    book,
    onBookClick: _onClick,
    onBookDeleted: () => onBookDeleted?.(book.id),
  });
  const shelfCreation = useCreateShelfWithBook({
    bookId: book.id,
  });
  const modals = useBookCardModals();
  const { isNavigating, navigateToReader } = useBookNavigation(book);

  // Layout selection strategy
  const layouts = {
    default: BookCardDefaultLayout,
    compact: BookCardCompactLayout,
  };
  const Layout = layouts[variant];

  // Handlers
  const handleClick = useCallback(() => {
    if (_onClick) {
      _onClick(book);
    }
  }, [_onClick, book]);

  const handleKeyDown = createEnterSpaceHandler(handleClick);
  const handleReadClick = isNavigating ? undefined : navigateToReader;

  return (
    <>
      <Layout
        selected={selected}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        ariaLabel={getBookCardAriaLabel(book, selected)}
        cover={
          <>
            <BookCardCover
              title={book.title}
              thumbnailUrl={book.thumbnail_url}
            />
            {showActions && variant === "default" && (
              <div className="hidden md:block">
                <BookCardOverlay selected={selected}>
                  {!selected && (
                    <BookCardCenterActions
                      onReadClick={handleReadClick}
                      onInfoClick={handleClick}
                      isReading={isNavigating}
                    />
                  )}
                  <BookCardActions
                    book={book}
                    allBooks={allBooks}
                    selected={selected}
                    showSelection={showSelection}
                    onEdit={onEdit}
                    menuProps={{
                      buttonRef: menu.menuButtonRef,
                      isMenuOpen: menu.isMenuOpen,
                      onToggle: menu.handleMenuToggle,
                      variant: "grid",
                    }}
                  />
                </BookCardOverlay>
              </div>
            )}
          </>
        }
        metadata={
          <BookCardMetadata title={book.title} authors={book.authors} />
        }
        actions={
          showActions && (
            <BookCardActions
              book={book}
              allBooks={allBooks}
              selected={selected}
              showSelection={showSelection}
              onEdit={onEdit}
              variant="mobile"
              menuProps={{
                buttonRef: menu.menuButtonRef,
                isMenuOpen: menu.isMenuOpen,
                onToggle: menu.handleMenuToggle,
                variant: "mobile",
              }}
            />
          )
        }
      />

      {showActions && (
        <>
          <BookCardMenu
            isOpen={menu.isMenuOpen}
            onClose={menu.handleMenuClose}
            buttonRef={menu.menuButtonRef}
            cursorPosition={menu.cursorPosition}
            book={book}
            onBookInfo={menuActions.handleBookInfo}
            onMoveToLibrary={menuActions.handleMoveToLibrary}
            onConvert={menuActions.handleConvert}
            onDelete={menuActions.handleDelete}
            onMore={menuActions.handleMore}
            isSendDisabled={menuActions.isSendDisabled}
            onOpenAddToShelfModal={modals.openAddToShelf}
          />
          <BookCardModals
            book={book}
            deleteState={menuActions.deleteConfirmation}
            shelfState={shelfCreation}
            addToShelfState={{
              show: modals.showAddToShelfModal,
              onClose: modals.closeAddToShelf,
              onSuccess: menu.handleMenuClose,
            }}
          />
        </>
      )}
    </>
  );
}
