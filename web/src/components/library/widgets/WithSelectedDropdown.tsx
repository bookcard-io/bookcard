"use client";

import styles from "./WithSelectedDropdown.module.scss";

export interface WithSelectedDropdownProps {
  /**
   * Callback fired when the dropdown is clicked.
   */
  onClick?: () => void;
}

/**
 * Dropdown button component for bulk actions on selected items.
 *
 * Provides a dropdown interface for performing actions on multiple selected items.
 */
export function WithSelectedDropdown({ onClick }: WithSelectedDropdownProps) {
  const handleClick = () => {
    onClick?.();
  };

  return (
    <button
      type="button"
      className={styles.dropdown}
      onClick={handleClick}
      aria-label="Actions with selected items"
      aria-haspopup="true"
    >
      <span className={styles.dropdownText}>With selected</span>
      <i
        className={`pi pi-chevron-down ${styles.chevronIcon}`}
        aria-hidden="true"
      />
    </button>
  );
}
