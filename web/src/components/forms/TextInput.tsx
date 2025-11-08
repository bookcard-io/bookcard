"use client";

import { forwardRef } from "react";
import styles from "./TextInput.module.scss";

export interface TextInputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Label text for the input. */
  label?: string;
  /** Error message to display. */
  error?: string;
  /** Helper text to display below input. */
  helperText?: string;
}

/**
 * Reusable text input component.
 *
 * Follows SRP by focusing solely on text input rendering and styling.
 * Uses forwardRef for proper ref forwarding (IOC).
 */
export const TextInput = forwardRef<HTMLInputElement, TextInputProps>(
  ({ label, error, helperText, className, ...props }, ref) => {
    return (
      <div className={styles.container}>
        {label && (
          <label htmlFor={props.id} className={styles.label}>
            {label}
          </label>
        )}
        <input
          ref={ref}
          type="text"
          className={`${styles.input} ${error ? styles.inputError : ""} ${className || ""}`}
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

TextInput.displayName = "TextInput";
