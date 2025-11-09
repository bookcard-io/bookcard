"use client";

import styles from "./RatingDisplay.module.scss";
import { RatingStars } from "./RatingStars";

export interface RatingDisplayProps {
  /** Current rating value (0-5). */
  value: number | null;
  /** Whether to show rating text (e.g., "3 / 5"). */
  showText?: boolean;
  /** Size variant for stars. */
  size?: "small" | "medium" | "large";
  /** Additional CSS class name. */
  className?: string;
}

/**
 * Read-only rating display component.
 *
 * Displays book rating as stars. Used for viewing ratings
 * in read-only contexts like book headers and cards.
 * Follows SRP by focusing solely on rating display.
 */
export function RatingDisplay({
  value,
  showText = false,
  size = "medium",
  className,
}: RatingDisplayProps) {
  if (value === null || value === undefined) {
    return null;
  }

  return (
    <div className={`${styles.container} ${className || ""}`}>
      <RatingStars
        value={value}
        interactive={false}
        showText={showText}
        size={size}
      />
    </div>
  );
}
