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

import { StatusPill } from "@/components/common/StatusPill";
import { cn } from "@/libs/utils";

export interface ReadingProgressIndicatorProps {
  /** Progress value (0.0 to 1.0). */
  progress: number;
  /** Read status (optional). */
  readStatus?: "not_read" | "reading" | "read" | null;
  /** Whether to show read status badge. */
  showStatus?: boolean;
  /** Optional className. */
  className?: string;
  /** Size variant. */
  size?: "small" | "medium" | "large";
}

/**
 * Reading progress indicator component.
 *
 * Displays a small progress bar and optional read status badge.
 * For use on book cards and list items.
 * Follows SRP by focusing solely on progress visualization.
 *
 * Parameters
 * ----------
 * props : ReadingProgressIndicatorProps
 *     Component props including progress and optional status.
 */
export function ReadingProgressIndicator({
  progress,
  readStatus,
  showStatus = false,
  className,
  size = "small",
}: ReadingProgressIndicatorProps) {
  const percentage = Math.round(progress * 100);

  const sizeClasses = {
    small: {
      bar: "h-1",
      text: "text-[10px]",
      pill: "tiny" as const,
    },
    medium: {
      bar: "h-1.5",
      text: "text-xs",
      pill: "small" as const,
    },
    large: {
      bar: "h-2",
      text: "text-sm",
      pill: "default" as const,
    },
  };

  const classes = sizeClasses[size];

  const getStatusPill = () => {
    if (!showStatus || !readStatus) {
      return null;
    }

    switch (readStatus) {
      case "read":
        return (
          <StatusPill
            label="Read"
            icon="pi pi-check"
            variant="success"
            size={classes.pill}
          />
        );
      case "reading":
        return (
          <StatusPill
            label="Reading"
            icon="pi pi-book"
            variant="info"
            size={classes.pill}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <div className="flex items-center justify-between gap-2">
        <div
          className={cn(
            "flex-1 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700",
            classes.bar,
          )}
        >
          <div
            className="h-full bg-primary-a0 transition-all duration-300 ease-out"
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span
          className={cn(
            "font-medium text-gray-600 dark:text-gray-400",
            classes.text,
          )}
        >
          {percentage}%
        </span>
      </div>
      {getStatusPill()}
    </div>
  );
}
