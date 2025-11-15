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
        className={cn(
          // Base styles
          "inline-flex items-center justify-center gap-2 font-inherit font-medium",
          "cursor-pointer rounded-md border border-solid",
          "transition-[background-color_0.2s,opacity_0.2s,transform_0.1s] ease-in-out",
          "leading-normal",
          // Focus styles
          "focus:shadow-[0_0_0_3px_rgba(144,170,249,0.3)] focus:outline-none",
          // Disabled styles
          "disabled:cursor-not-allowed disabled:opacity-50",
          // Active styles (disabled buttons won't respond to active state)
          "active:scale-[0.98]",
          // Variant styles
          variant === "primary" && [
            "bg-primary-a0 text-[var(--color-text-primary-a0)]",
            "border-primary-a20",
            "hover:bg-primary-a10",
          ],
          variant === "secondary" && [
            "border-surface-a30 bg-surface-a10 text-text-a0",
            "hover:bg-surface-a20",
          ],
          variant === "danger" && [
            "bg-danger-a0 text-[var(--color-white)]",
            "border-danger-a10",
            "hover:bg-danger-a10",
          ],
          variant === "ghost" && [
            "bg-transparent text-text-a20",
            "border-primary-a0",
            "hover:bg-surface-a10 hover:text-text-a0",
          ],
          variant === "success" && [
            "bg-success-a0 text-[var(--color-white)]",
            "border-success-a10",
            "hover:bg-success-a10",
            "active:bg-success-a0",
          ],
          // Size styles
          size === "small" && "px-4 py-2 text-sm",
          size === "medium" && "px-6 py-3 text-base",
          size === "large" && "px-8 py-4 text-lg",
          className,
        )}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <>
            <span
              className="h-4 w-4 animate-spin rounded-full border-2 border-transparent border-t-current"
              aria-hidden="true"
            />
            <span className="opacity-80">Loading...</span>
          </>
        ) : (
          children
        )}
      </button>
    );
  },
);

Button.displayName = "Button";
