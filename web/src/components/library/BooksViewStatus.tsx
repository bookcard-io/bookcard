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
import { Button } from "@/components/forms/Button";
import { useScrollNavigation } from "@/hooks/useScrollNavigation";
import { useStickyStatus } from "@/hooks/useStickyStatus";
import { cn } from "@/libs/utils";

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
 * Displays current count and total, with optional action buttons and scroll
 * navigation controls when sticky. Follows SRP by handling only presentation.
 * Follows IOC by accepting actions and delegating scroll logic to hooks.
 * Follows SOC by separating scroll navigation from status display.
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
  const { statusRef, isSticky, opacity } = useStickyStatus();
  const { scrollToTop, scrollUp, scrollDown } = useScrollNavigation();

  if (total === 0) {
    return null;
  }

  return (
    <div
      ref={statusRef}
      className={cn(
        "relative flex items-center justify-between px-8 py-4",
        isSticky &&
          "sticky top-0 z-10 border-surface-a10 border-b-1 border-solid",
      )}
    >
      {/* Background layer with opacity */}
      {isSticky && (
        <div
          className="absolute inset-0 bg-surface-a0 transition-opacity duration-200"
          style={{
            opacity,
            backdropFilter: opacity > 0 ? "blur(8px)" : "none",
          }}
        />
      )}
      {/* Content layer */}
      <div className="relative z-10 flex w-full items-center justify-between">
        <div className="text-center text-sm text-text-a40">
          {hasMore
            ? `Scroll for more (${currentCount} of ${total})`
            : `${currentCount} of ${total} books`}
        </div>
        <div className="flex items-center gap-2">
          {actions && <div className="flex items-center">{actions}</div>}
          {isSticky && (
            <>
              <Button
                variant="primary"
                size="xsmall"
                onClick={scrollToTop}
                aria-label="Scroll to top"
              >
                <i className="pi pi-angle-double-up" aria-hidden="true" />
                <span>Top</span>
              </Button>
              <Button
                variant="primary"
                size="xsmall"
                onClick={scrollUp}
                aria-label="Scroll up"
              >
                <i className="pi pi-angle-up" aria-hidden="true" />
                <span>Up</span>
              </Button>
              <Button
                variant="primary"
                size="xsmall"
                onClick={scrollDown}
                aria-label="Scroll down"
              >
                <i className="pi pi-angle-down" aria-hidden="true" />
                <span>Down</span>
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
