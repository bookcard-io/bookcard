"use client";

import { forwardRef } from "react";
import styles from "./TextArea.module.scss";

export interface TextAreaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Label text for the textarea. */
  label?: string;
  /** Error message to display. */
  error?: string;
  /** Helper text to display below textarea. */
  helperText?: string;
  /** Optional class for the outer wrapper to control grid placement. */
  wrapperClassName?: string;
}

/**
 * Reusable textarea component.
 *
 * Follows SRP by focusing solely on textarea rendering and styling.
 * Uses forwardRef for proper ref forwarding (IOC).
 */
export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  (
    { label, error, helperText, className, wrapperClassName, ...props },
    ref,
  ) => {
    return (
      <div className={`${styles.container} ${wrapperClassName || ""}`}>
        {label && (
          <label htmlFor={props.id} className={styles.label}>
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          className={`${styles.textarea} ${error ? styles.textareaError : ""} ${className || ""}`}
          aria-invalid={error ? "true" : "false"}
          aria-describedby={
            error || helperText
              ? `${props.id}-${error ? "error" : "helper"}`
              : undefined
          }
          {...props}
        />
        {error && (
          <span id={`${props.id}-error`} className={styles.error} role="alert">
            {error}
          </span>
        )}
        {helperText && !error && (
          <span id={`${props.id}-helper`} className={styles.helperText}>
            {helperText}
          </span>
        )}
      </div>
    );
  },
);

TextArea.displayName = "TextArea";
