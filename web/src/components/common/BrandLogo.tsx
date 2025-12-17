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

import Link from "next/link";
import { cn } from "@/libs/utils";

export interface BrandLogoProps {
  /** Whether to show the brand name text. */
  showText?: boolean;
  /** Optional className for the container. */
  className?: string;
  /** Optional className for the logo image. */
  logoClassName?: string;
  /** Optional className for the brand text. */
  textClassName?: string;
}

/**
 * Reusable brand logo component.
 *
 * Displays the Fundamental logo and brand name.
 * Follows DRY by centralizing logo/brand display logic.
 * Follows SRP by only handling logo/brand rendering.
 *
 * Parameters
 * ----------
 * props : BrandLogoProps
 *     Component props including visibility and styling options.
 *
 * Examples
 * --------
 * ```tsx
 * <BrandLogo showText={true} />
 * <BrandLogo showText={false} className="gap-2" />
 * ```
 */
export function BrandLogo({
  showText = true,
  className,
  logoClassName,
  textClassName,
}: BrandLogoProps) {
  return (
    <Link
      href="/"
      className={cn("flex items-center gap-3", className)}
      aria-label="Go to home page"
    >
      <img
        src="/reading-logo.png"
        alt="Fundamental Logo"
        width={24}
        height={24}
        className={cn("h-6 min-h-6 w-6 min-w-6 shrink-0", logoClassName)}
      />
      {showText && (
        <span
          className={cn(
            "whitespace-nowrap font-medium text-[var(--color-text-a0)] text-lg tracking-wide",
            textClassName,
          )}
        >
          Fundamental
        </span>
      )}
    </Link>
  );
}
