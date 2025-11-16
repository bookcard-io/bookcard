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

import type { ReactNode } from "react";

export interface BooksViewStatusProps {
  /** Current number of books loaded. */
  currentCount: number;
  /** Total number of books available. */
  total: number;
  /** Whether there are more books to load. */
  hasMore: boolean;
  /** Optional action buttons to display on the right. */
  actions?: ReactNode;
}

/**
 * Status bar component for books view.
 *
 * Displays current count and total, with optional action buttons.
 * Follows SRP by handling only status display.
 * Follows IOC by accepting actions as children.
 *
 * Parameters
 * ----------
 * props : BooksViewStatusProps
 *     Status information and optional actions.
 */
export function BooksViewStatus({
  currentCount,
  total,
  hasMore,
  actions,
}: BooksViewStatusProps) {
  if (total === 0) {
    return null;
  }

  return (
    <div className="flex items-center justify-between px-8 pb-4">
      <div className="text-left text-sm text-text-a40">
        {hasMore
          ? `Scroll for more (${currentCount} of ${total})`
          : `${currentCount} of ${total} books`}
      </div>
      {actions && <div className="flex items-center">{actions}</div>}
    </div>
  );
}
