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
import { BookCardReadingCorner } from "@/components/library/BookCardReadingCorner";
import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import { useUser } from "@/contexts/UserContext";
import { useBookCardMenu } from "@/hooks/useBookCardMenu";
import { useBookCardMenuActions } from "@/hooks/useBookCardMenuActions";
import { useBookCardModals } from "@/hooks/useBookCardModals";
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
  /** Whether to display the library badge on the book card. Defaults to false. */
  showLibraryBadge?: boolean;
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
  showSelection: showSelectionProp = false,
  hideActions = false,
  variant = "default",
  showLibraryBadge = false,
}: BookCardProps) {
  const { isSelected } = useSelectedBooks();
  const { user } = useUser();
  const isGuest = !user;
  const selected = isSelected(book.id);
  const showActions = !hideActions;
  const showSelection = showSelectionProp && !isGuest;

  // Hooks for logic and state
  const menu = useBookCardMenu();
  const menuActions = useBookCardMenuActions({
    book,
    onBookClick: _onClick,
    onBookDeleted: () => onBookDeleted?.(book.id),
  });
  const shelfCreation = useCreateShelfWithBook({
    bookId: book.id,
    libraryId: book.library_id ?? 0,
  });
  const modals = useBookCardModals();

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

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "wanted":
        return "bg-surface-tonal-a40/50 text-text-a0 backdrop-blur-md";
      case "searching":
        return "bg-info-a0/50 text-white backdrop-blur-md";
      case "downloading":
        return "bg-info-a0/50 text-white backdrop-blur-md";
      case "seeding":
        return "bg-success-a0/50 text-white backdrop-blur-md";
      case "paused":
      case "stalled":
        return "bg-warning-a0/50 text-white backdrop-blur-md";
      case "failed":
        return "bg-danger-a0/50 text-white backdrop-blur-md";
      case "completed":
        return "bg-success-a0/50 text-white backdrop-blur-md";
      default:
        return "bg-surface-tonal-a40/50 text-text-a0 backdrop-blur-md";
    }
  };

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
            {book.is_virtual && book.tracking_status && (
              <div
                className={`absolute top-2 right-2 z-10 rounded px-2 py-0.5 font-medium text-[0.725rem] uppercase tracking-wider shadow-sm ${getStatusColor(book.tracking_status)}`}
              >
                {book.tracking_status}
              </div>
            )}
            {book.is_virtual ? null : (
              <BookCardReadingCorner
                bookId={book.id}
                readingSummary={book.reading_summary ?? null}
              />
            )}
            {showActions && variant === "default" && !book.is_virtual && (
              <div className="hidden md:block">
                <BookCardOverlay selected={selected}>
                  {!selected && <BookCardCenterActions book={book} />}
                  <BookCardActions
                    book={book}
                    allBooks={allBooks}
                    selected={selected}
                    showSelection={showSelection}
                    onEdit={isGuest ? undefined : onEdit}
                    showMenu
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
          <BookCardMetadata
            title={book.title}
            authors={book.authors}
            libraryName={book.library_name}
            showLibraryBadge={showLibraryBadge}
          />
        }
        actions={
          showActions &&
          !book.is_virtual && (
            <BookCardActions
              book={book}
              allBooks={allBooks}
              selected={selected}
              showSelection={showSelection}
              onEdit={isGuest ? undefined : onEdit}
              showMenu
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

      {showActions && !book.is_virtual && (
        <>
          <BookCardMenu
            isOpen={menu.isMenuOpen}
            onClose={menu.handleMenuClose}
            buttonRef={menu.menuButtonRef}
            cursorPosition={menu.cursorPosition}
            book={book}
            actions={menuActions}
            onOpenAddToShelfModal={modals.openAddToShelf}
          />
          {!isGuest && (
            <BookCardModals
              book={book}
              deleteState={menuActions.deleteConfirmation}
              shelfState={shelfCreation}
              addToShelfState={{
                show: modals.showAddToShelfModal,
                onClose: modals.closeAddToShelf,
                onSuccess: menu.handleMenuClose,
              }}
              conversionState={menuActions.conversionState}
            />
          )}
        </>
      )}
    </>
  );
}
