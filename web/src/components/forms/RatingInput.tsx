"use client";

import styles from "./RatingInput.module.scss";

export interface RatingInputProps {
  /** Label text for the input. */
  label?: string;
  /** Current rating value (0-5). */
  value: number | null;
  /** Callback when rating changes. */
  onChange: (rating: number | null) => void;
  /** Error message to display. */
  error?: string;
  /** Helper text to display. */
  helperText?: string;
  /** Input ID for accessibility. */
  id?: string;
}

/**
 * Rating input component for selecting a rating from 0-5.
 *
 * Follows SRP by focusing solely on rating selection.
 * Uses controlled component pattern (IOC via props).
 */
export function RatingInput({
  label,
  value,
  onChange,
  error,
  helperText,
  id = "rating-input",
}: RatingInputProps) {
  const handleStarClick = (rating: number) => {
    if (value === rating) {
      // Clicking the same rating clears it
      onChange(null);
    } else {
      onChange(rating);
    }
  };

  return (
    <div className={styles.container}>
      {label && (
        <label htmlFor={id} className={styles.label}>
          {label}
        </label>
      )}
      <div
        className={styles.starsContainer}
        role="radiogroup"
        aria-label={label || "Rating"}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={
          error || helperText
            ? `${id}-${error ? "error" : "helper"}`
            : undefined
        }
      >
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            className={`${styles.star} ${value !== null && star <= value ? styles.starFilled : ""}`}
            onClick={() => handleStarClick(star)}
            aria-label={`Rate ${star} out of 5`}
            aria-pressed={value !== null && star <= value}
          >
            ★
          </button>
        ))}
        {value !== null && (
          <span className={styles.ratingText}>{value} / 5</span>
        )}
      </div>
      {error && (
        <span id={`${id}-error`} className={styles.error} role="alert">
          {error}
        </span>
      )}
      {helperText && !error && (
        <span id={`${id}-helper`} className={styles.helperText}>
          {helperText}
        </span>
      )}
    </div>
  );
}
