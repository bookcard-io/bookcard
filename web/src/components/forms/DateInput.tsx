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
      <div className="flex w-full flex-col gap-2">
        {label && (
          <label
            htmlFor={props.id}
            className="font-medium text-sm text-text-a10 leading-normal"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          type="date"
          className={cn(
            // Base input styles
            "w-full rounded-lg border border-surface-a20 bg-surface-a0 px-4 py-3",
            "font-inherit text-base text-text-a0 leading-normal",
            "transition-[border-color,box-shadow,background-color] duration-200",
            // Placeholder
            "placeholder:text-text-a40",
            // Focus state
            "focus:border-primary-a0 focus:bg-surface-a10 focus:outline-none",
            "focus:shadow-[0_0_0_3px_rgba(144,170,249,0.1)]",
            // Hover state (focus styles will override when focused)
            "hover:border-surface-a30",
            // Disabled state
            "disabled:cursor-not-allowed disabled:opacity-50",
            // Calendar picker indicator
            "[&::-webkit-calendar-picker-indicator]:cursor-pointer [&::-webkit-calendar-picker-indicator]:[filter:invert(0.8)]",
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
            className="text-danger-a10 text-sm leading-normal"
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
