"use client";

import styles from "./SortByDropdown.module.scss";

export interface SortByDropdownProps {
  /**
   * Callback fired when the dropdown is clicked.
   */
  onClick?: () => void;
}

/**
 * Dropdown button component for sorting options.
 *
 * Provides a dropdown interface for selecting sort criteria.
 */
export function SortByDropdown({ onClick }: SortByDropdownProps) {
  const handleClick = () => {
    onClick?.();
  };

  return (
    <button
      type="button"
      className={styles.dropdown}
      onClick={handleClick}
      aria-label="Sort options"
      aria-haspopup="true"
    >
      <span className={styles.dropdownText}>Sort by</span>
      <i
        className={`pi pi-chevron-down ${styles.chevronIcon}`}
        aria-hidden="true"
      />
    </button>
  );
}
