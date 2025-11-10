"use client";

import { forwardRef } from "react";
import { cn } from "@/libs/utils";

export interface DateInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  /** Label text for the input. */
  label?: string;
  /** Error message to display. */
  error?: string;
  /** Helper text to display below input. */
  helperText?: string;
}

/**
 * Reusable date input component.
 *
 * Follows SRP by focusing solely on date input rendering and styling.
 * Uses forwardRef for proper ref forwarding (IOC).
 */
export const DateInput = forwardRef<HTMLInputElement, DateInputProps>(
  ({ label, error, helperText, className, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-2 w-full">
        {label && (
          <label
            htmlFor={props.id}
            className="text-sm font-medium text-text-a10 leading-normal"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          type="date"
          className={cn(
            // Base input styles
            "w-full px-4 py-3 bg-surface-a0 border border-surface-a20 rounded-lg",
            "text-text-a0 text-base leading-normal font-inherit",
            "transition-[border-color,box-shadow,background-color] duration-200",
            // Placeholder
            "placeholder:text-text-a40",
            // Focus state
            "focus:outline-none focus:border-primary-a0 focus:bg-surface-a10",
            "focus:shadow-[0_0_0_3px_rgba(144,170,249,0.1)]",
            // Hover state (focus styles will override when focused)
            "hover:border-surface-a30",
            // Disabled state
            "disabled:opacity-50 disabled:cursor-not-allowed",
            // Calendar picker indicator
            "[&::-webkit-calendar-picker-indicator]:[filter:invert(0.8)] [&::-webkit-calendar-picker-indicator]:cursor-pointer",
            // Error state
            error && [
              "border-danger-a0",
              "focus:border-danger-a0 focus:shadow-[0_0_0_3px_rgba(156,33,33,0.1)]",
            ],
            className,
          )}
          aria-invalid={error ? "true" : "false"}
          aria-describedby={
            error || helperText
              ? `${props.id}-${error ? "error" : "helper"}`
              : undefined
          }
          {...props}
        />
        {error && (
          <span
            id={`${props.id}-error`}
            className="text-sm text-danger-a10 leading-normal"
            role="alert"
          >
            {error}
          </span>
        )}
        {helperText && !error && (
          <span
            id={`${props.id}-helper`}
            className="text-sm text-text-a30 leading-normal"
          >
            {helperText}
          </span>
        )}
      </div>
    );
  },
);

DateInput.displayName = "DateInput";
