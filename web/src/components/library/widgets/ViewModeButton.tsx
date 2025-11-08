"use client";

import styles from "./ViewModeButton.module.scss";

export interface ViewModeButtonProps {
  /**
   * PrimeIcons class name(s) to display in the button.
   */
  iconClass: string;
  /**
   * Whether this view mode is currently active.
   */
  isActive?: boolean;
  /**
   * Callback fired when the button is clicked.
   */
  onClick?: () => void;
  /**
   * Accessible label for the button.
   */
  ariaLabel: string;
}

/**
 * Individual view mode toggle button component.
 *
 * Represents a single view mode option (e.g., grid, list, sort).
 * Follows SRP by handling only button UI and click events.
 */
export function ViewModeButton({
  iconClass,
  isActive = false,
  onClick,
  ariaLabel,
}: ViewModeButtonProps) {
  const handleClick = () => {
    onClick?.();
  };

  return (
    <button
      type="button"
      className={`${styles.viewModeButton} ${isActive ? styles.active : ""}`}
      onClick={handleClick}
      aria-label={ariaLabel}
      aria-pressed={isActive}
    >
      <i className={`pi ${iconClass} ${styles.icon}`} aria-hidden="true" />
    </button>
  );
}
