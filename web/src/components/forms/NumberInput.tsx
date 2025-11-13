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

import { forwardRef } from "react";
import { cn } from "@/libs/utils";

export interface NumberInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  /** Label text for the input. */
  label?: string;
  /** Error message to display. */
  error?: string;
  /** Helper text to display below input. */
  helperText?: string;
  /** Minimum value. */
  min?: number;
  /** Maximum value. */
  max?: number;
  /** Step value for increment/decrement. */
  step?: number;
}

/**
 * Reusable number input component.
 *
 * Follows SRP by focusing solely on number input rendering and styling.
 * Uses forwardRef for proper ref forwarding (IOC).
 */
export const NumberInput = forwardRef<HTMLInputElement, NumberInputProps>(
  ({ label, error, helperText, className, ...props }, ref) => {
    return (
      <div className="relative flex w-full flex-col gap-2">
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
          type="number"
          className={cn(
            "w-full rounded-lg border border-surface-a20 bg-surface-a0 px-4 py-3",
            "font-inherit text-base text-text-a0 leading-normal",
            "transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s]",
            "placeholder:text-text-a40",
            "focus:border-primary-a0 focus:bg-surface-a10 focus:outline-none",
            "focus:shadow-[var(--shadow-focus-ring)]",
            "hover:not(:focus):border-surface-a30",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "[&::-webkit-inner-spin-button]:opacity-100 [&::-webkit-outer-spin-button]:opacity-100",
            error && [
              "border-danger-a0",
              "focus:border-danger-a0 focus:shadow-[var(--shadow-focus-ring-danger)]",
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

NumberInput.displayName = "NumberInput";
