"use client";

import type React from "react";
import type { SVGProps } from "react";
import styles from "./ViewModeButton.module.scss";

export interface ViewModeButtonProps {
  /**
   * Icon component to display in the button.
   */
  icon: React.ComponentType<SVGProps<SVGSVGElement>>;
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
 */
export function ViewModeButton({
  icon: Icon,
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
      <Icon className={styles.icon} aria-hidden="true" />
    </button>
  );
}
