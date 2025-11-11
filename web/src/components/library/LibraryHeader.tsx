"use client";

import { PageHeader } from "@/components/layout/PageHeader";
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
 * Standard action bar buttons (Profile, Admin) are automatically included
 * via the HeaderActionBarButtons component in PageLayout.
 */
export function LibraryHeader({ onAddBooksClick }: LibraryHeaderProps) {
  return (
    <PageHeader title="My Library">
      <AddBooksButton onClick={onAddBooksClick} />
    </PageHeader>
  );
}
