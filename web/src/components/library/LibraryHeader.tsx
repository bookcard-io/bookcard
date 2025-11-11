"use client";

import { AddBooksButton } from "./widgets/AddBooksButton";

export interface LibraryHeaderProps {
  /**
   * Callback fired when "Add Books" button is clicked.
   */
  onAddBooksClick?: () => void;
}

/**
 * Header component for the library page.
 *
 * Displays the "My Library" title at the top of the main content area
 * with the "Add Books" button positioned on the right.
 */
export function LibraryHeader({ onAddBooksClick }: LibraryHeaderProps) {
  return (
    <header className="flex items-center justify-between px-8 pt-6 pb-4">
      <h1 className="m-0 font-semibold text-[32px] text-[var(--color-text-a0)] leading-[1.2]">
        My Library
      </h1>
      <div className="flex shrink-0 items-center">
        <AddBooksButton onClick={onAddBooksClick} />
      </div>
    </header>
  );
}
