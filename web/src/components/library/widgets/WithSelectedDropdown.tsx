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

import { useMemo, useRef, useState } from "react";
import { AddToShelfModal } from "@/components/library/AddToShelfModal";
import { BookMergeModal } from "@/components/library/BookMergeModal";
import { WithSelectedMenu } from "@/components/library/widgets/WithSelectedMenu";
import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import { useWithSelectedMenuActions } from "@/hooks/useWithSelectedMenuActions";
import { cn } from "@/libs/utils";

export interface WithSelectedDropdownProps {
  /**
   * Callback fired when the dropdown is clicked.
   */
  onClick?: () => void;
  /**
   * Whether Send action is disabled.
   */
  isSendDisabled?: boolean;
  /**
   * Whether the dropdown is disabled.
   */
  disabled?: boolean;
}

/**
 * Dropdown button component for bulk actions on selected items.
 *
 * Provides a dropdown interface for performing actions on multiple selected items.
 * Follows SRP by handling only dropdown display and item selection.
 * Uses IOC via callback props for actions.
 * Follows DRY by using shared DropdownMenuItem components.
 */
export function WithSelectedDropdown({
  onClick,
  isSendDisabled: isSendDisabledProp = false,
  disabled = false,
}: WithSelectedDropdownProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [cursorPosition, setCursorPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const { selectedBookIds, books } = useSelectedBooks();

  // Get all selected books
  const selectedBooks = useMemo(() => {
    if (selectedBookIds.size === 0 || books.length === 0) {
      return [];
    }
    return books.filter((book) => selectedBookIds.has(book.id));
  }, [selectedBookIds, books]);

  const actions = useWithSelectedMenuActions({
    selectedBooks,
  });

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (disabled) {
      return;
    }
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      // Align left edge of menu with left edge of button
      setCursorPosition({ x: rect.left, y: rect.bottom });
    } else {
      setCursorPosition({ x: e.clientX, y: e.clientY });
    }
    setIsMenuOpen((prev) => !prev);
    onClick?.();
  };

  const handleMenuClose = () => {
    setIsMenuOpen(false);
  };

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        className={cn(
          "btn-tonal group flex cursor-pointer items-center gap-2 whitespace-nowrap px-4 py-2.5 font-inherit",
        )}
        onClick={handleClick}
        aria-label="Actions with selected items"
        aria-haspopup="true"
        aria-expanded={isMenuOpen}
        data-with-selected-button
      >
        <span className="leading-none">With selected</span>
        <i
          className={cn(
            "pi pi-chevron-down h-4 w-4 flex-shrink-0 text-text-a30 transition-[color,transform] duration-200 group-hover:text-text-a0",
            isMenuOpen && "rotate-180",
          )}
          aria-hidden="true"
        />
      </button>
      <WithSelectedMenu
        isOpen={isMenuOpen}
        onClose={handleMenuClose}
        buttonRef={buttonRef}
        cursorPosition={cursorPosition}
        selectedBooks={selectedBooks}
        actions={{
          ...actions,
          isSendDisabled: isSendDisabledProp || actions.isSendDisabled,
        }}
      />
      {actions.addToShelfState.isOpen && (
        <AddToShelfModal
          onClose={() => {
            actions.addToShelfState.close();
            handleMenuClose();
          }}
          onSuccess={handleMenuClose}
        />
      )}
      {actions.mergeModalState.isOpen && (
        <BookMergeModal
          bookIds={selectedBooks.map((b) => b.id)}
          onClose={() => {
            actions.mergeModalState.close();
            handleMenuClose();
          }}
        />
      )}
    </>
  );
}
