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

export interface SelectProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {
  /** Label text for the select. */
  label?: string;
  /** Error message to display. */
  error?: string;
  /** Helper text to display below select. */
  helperText?: string;
  /** Options to display. */
  options?: Array<{
    value: string | number;
    label: string;
    disabled?: boolean;
  }>;
}

/**
 * Reusable select component.
 *
 * Follows SRP by focusing solely on select rendering and styling.
 * Uses forwardRef for proper ref forwarding (IOC).
 */
export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    { label, error, helperText, className, options, children, ...props },
    ref,
  ) => {
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
        <div className="w-full">
          <select
            ref={ref}
            className={cn(
              "h-11 w-full rounded-md border border-surface-a20 bg-surface-tonal-a10 px-3 py-2",
              "text-sm text-text-a0",
              "transition-[border-color,background-color] duration-200",
              "hover:border-surface-a30",
              "focus:border-primary-a0 focus:bg-surface-tonal-a0 focus:outline-none",
              "disabled:cursor-not-allowed disabled:opacity-50",
              error && "border-danger-a0 focus:border-danger-a0",
              className,
            )}
            aria-invalid={error ? "true" : "false"}
            aria-describedby={
              error || helperText
                ? `${props.id}-${error ? "error" : "helper"}`
                : undefined
            }
            {...props}
          >
            {options
              ? options.map((opt) => (
                  <option
                    key={opt.value}
                    value={opt.value}
                    disabled={opt.disabled}
                  >
                    {opt.label}
                  </option>
                ))
              : children}
          </select>
        </div>
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

Select.displayName = "Select";
