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

import styles from "./RatingDisplay.module.scss";
import { RatingStars } from "./RatingStars";

export interface RatingDisplayProps {
  /** Current rating value (0-5). */
  value: number | null;
  /** Whether to show rating text (e.g., "3 / 5"). */
  showText?: boolean;
  /** Size variant for stars. */
  size?: "small" | "medium" | "large";
  /** Additional CSS class name. */
  className?: string;
}

/**
 * Read-only rating display component.
 *
 * Displays book rating as stars. Used for viewing ratings
 * in read-only contexts like book headers and cards.
 * Follows SRP by focusing solely on rating display.
 */
export function RatingDisplay({
  value,
  showText = false,
  size = "medium",
  className,
}: RatingDisplayProps) {
  if (value === null || value === undefined) {
    return null;
  }

  return (
    <div className={`${styles.container} ${className || ""}`}>
      <RatingStars
        value={value}
        interactive={false}
        showText={showText}
        size={size}
      />
    </div>
  );
}
