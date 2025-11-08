"use client";

import styles from "./SortByDropdown.module.scss";
import type { SortField } from "./SortPanel";
import { SORT_OPTIONS } from "./SortPanel";

export interface SortByDropdownProps {
  /**
   * Currently selected sort field.
   */
  sortBy?: SortField;
  /**
   * Callback fired when the dropdown is clicked.
   */
  onClick?: () => void;
}

/**
 * Dropdown button component for sorting options.
 *
 * Provides a dropdown interface for selecting sort criteria.
 * Follows SRP by handling only UI display and click events.
 */
export function SortByDropdown({
  sortBy = "timestamp",
  onClick,
}: SortByDropdownProps) {
  const handleClick = () => {
    onClick?.();
  };

  const selectedOption = SORT_OPTIONS.find((opt) => opt.value === sortBy);
  const displayText = selectedOption?.label || "Sort by";

  return (
    <button
      type="button"
      className={styles.dropdown}
      onClick={handleClick}
      aria-label="Sort options"
      aria-haspopup="true"
      data-sort-button
    >
      <span className={styles.dropdownText}>{displayText}</span>
      <i
        className={`pi pi-chevron-down ${styles.chevronIcon}`}
        aria-hidden="true"
      />
    </button>
  );
}
