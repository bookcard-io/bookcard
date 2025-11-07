"use client";

import { Filter } from "@/icons/Filter";
import styles from "./FiltersButton.module.scss";

export interface FiltersButtonProps {
  /**
   * Callback fired when the filters button is clicked.
   */
  onClick?: () => void;
}

/**
 * Button component for opening the filters panel.
 *
 * Displays a filter icon and label for accessing filter options.
 */
export function FiltersButton({ onClick }: FiltersButtonProps) {
  const handleClick = () => {
    onClick?.();
  };

  return (
    <button
      type="button"
      className={styles.filtersButton}
      onClick={handleClick}
      aria-label="Open filters"
    >
      <Filter className={styles.filterIcon} aria-hidden="true" />
      <span className={styles.buttonText}>Filters</span>
    </button>
  );
}
