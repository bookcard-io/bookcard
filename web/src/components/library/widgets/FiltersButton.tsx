"use client";

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
      data-filters-button
    >
      <i className="pi pi-filter" aria-hidden="true" />
      <span className={styles.buttonText}>Filters</span>
    </button>
  );
}
