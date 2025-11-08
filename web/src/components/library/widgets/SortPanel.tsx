"use client";

import { useEffect, useRef } from "react";
import styles from "./SortPanel.module.scss";

export type SortField =
  | "title"
  | "author_sort"
  | "timestamp"
  | "pubdate"
  | "series_index";

export interface SortOption {
  /** Display label for the sort option. */
  label: string;
  /** Backend field name. */
  value: SortField;
}

export const SORT_OPTIONS: SortOption[] = [
  { label: "Title", value: "title" },
  { label: "Author", value: "author_sort" },
  { label: "Added date", value: "timestamp" },
  { label: "Modified date", value: "pubdate" },
  { label: "Size", value: "series_index" },
];

export interface SortPanelProps {
  /**
   * Currently selected sort field.
   */
  sortBy?: SortField;
  /**
   * Callback fired when a sort option is selected.
   */
  onSortByChange?: (sortBy: SortField) => void;
  /**
   * Callback fired when the panel should be closed.
   */
  onClose?: () => void;
}

/**
 * Sort panel component for selecting sort criteria.
 *
 * Displays a dropdown menu with sort options (Title, Author, Added date, etc.).
 * Follows SRP by handling only sort selection UI.
 */
export function SortPanel({
  sortBy = "timestamp",
  onSortByChange,
  onClose,
}: SortPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  // Handle click outside to close panel
  // Exclude clicks on the SortByDropdown button
  useEffect(() => {
    if (!onClose) {
      return;
    }

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;

      // Don't close if clicking on the SortByDropdown button or its children
      const isSortButton = target.closest("[data-sort-button]");
      if (isSortButton) {
        return;
      }

      // Don't close if clicking inside the panel
      if (panelRef.current?.contains(target)) {
        return;
      }

      // Close if clicking outside
      onClose();
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [onClose]);

  const handleOptionClick = (option: SortOption) => {
    onSortByChange?.(option.value);
    onClose?.();
  };

  return (
    <div className={styles.sortPanel} ref={panelRef}>
      {SORT_OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          className={`${styles.sortOption} ${
            sortBy === option.value ? styles.active : ""
          }`}
          onClick={() => handleOptionClick(option)}
          aria-label={`Sort by ${option.label}`}
          aria-pressed={sortBy === option.value}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
