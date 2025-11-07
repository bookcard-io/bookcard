"use client";

import { AddBooksButton } from "./widgets/AddBooksButton";
import styles from "./LibraryHeader.module.scss";

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
    <header className={styles.header}>
      <h1 className={styles.title}>My Library</h1>
      <div className={styles.rightSection}>
        <AddBooksButton onClick={onAddBooksClick} />
      </div>
    </header>
  );
}
