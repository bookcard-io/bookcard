"use client";

import { forwardRef } from "react";
import styles from "./Button.module.scss";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Button variant style. */
  variant?: "primary" | "secondary" | "danger" | "ghost" | "success";
  /** Button size. */
  size?: "small" | "medium" | "large";
  /** Whether button is in loading state. */
  loading?: boolean;
}

/**
 * Reusable button component.
 *
 * Follows SRP by focusing solely on button rendering and styling.
 * Uses forwardRef for proper ref forwarding (IOC).
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "medium",
      loading = false,
      className,
      children,
      disabled,
      type = "button",
      ...props
    },
    ref,
  ) => {
    return (
      <button
        ref={ref}
        type={type}
        className={`${styles.button} ${styles[variant]} ${styles[size]} ${className || ""}`}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <>
            <span className={styles.spinner} aria-hidden="true" />
            <span className={styles.loadingText}>Loading...</span>
          </>
        ) : (
          children
        )}
      </button>
    );
  },
);

Button.displayName = "Button";
