// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

"use client";

import styles from "./RatingStars.module.scss";

export interface RatingStarsProps {
  /** Current rating value (0-5). */
  value: number | null;
  /** Whether stars are interactive (for input). */
  interactive?: boolean;
  /** Callback when a star is clicked (only used when interactive). */
  onStarClick?: (rating: number) => void;
  /** Whether to show rating text (e.g., "3 / 5"). */
  showText?: boolean;
  /** Size variant for stars. */
  size?: "small" | "medium" | "large";
  /** Additional CSS class name. */
  className?: string;
}

/**
 * Shared rating stars component.
 *
 * Displays 1-5 stars based on rating value. Can be used for both
 * read-only display and interactive input.
 * Follows SRP by focusing solely on star rendering.
 * Uses IOC via props for flexibility.
 */
export function RatingStars({
  value,
  interactive = false,
  onStarClick,
  showText = false,
  size = "medium",
  className,
}: RatingStarsProps) {
  const handleStarClick = (rating: number) => {
    if (interactive && onStarClick) {
      onStarClick(rating);
    }
  };

  const starElements = [1, 2, 3, 4, 5].map((star) => {
    const isFilled = value !== null && star <= value;
    const starClassName = `${styles.star} ${isFilled ? styles.starFilled : ""} ${styles[size]}`;

    if (interactive) {
      return (
        <button
          key={star}
          type="button"
          className={starClassName}
          onClick={() => handleStarClick(star)}
          aria-label={`Rate ${star} out of 5`}
          aria-pressed={isFilled}
        >
          ★
        </button>
      );
    }

    return (
      <span key={star} className={starClassName}>
        ★
      </span>
    );
  });

  return (
    <div className={`${styles.starsContainer} ${className || ""}`}>
      {starElements}
      {showText && value !== null && (
        <span className={styles.ratingText}>{value} / 5</span>
      )}
    </div>
  );
}
