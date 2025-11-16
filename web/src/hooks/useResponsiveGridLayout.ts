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

import { useEffect, useState } from "react";

export interface ResponsiveGridLayout {
  /** Number of columns to render based on available width and breakpoints. */
  columnCount: number;
  /** Target card width in pixels (clamped to BookCard max width). */
  cardWidth: number;
  /** Gap between cards in pixels. */
  gap: number;
}

/**
 * Responsive layout hook for the books grid.
 *
 * Computes column count, card width, and gap based on container width and
 * breakpoint-like thresholds that mirror the Tailwind grid configuration.
 * This keeps visual spacing consistent while allowing the virtualizer to
 * work with explicit row/column calculations.
 * Follows SRP by managing only responsive layout concerns.
 * Follows IOC by accepting container ref as dependency.
 *
 * Parameters
 * ----------
 * containerRef : React.RefObject<HTMLDivElement | null>
 *     Ref to the container element whose width determines the layout.
 *
 * Returns
 * -------
 * ResponsiveGridLayout
 *     Layout configuration including column count, card width, and gap.
 */
export function useResponsiveGridLayout(
  containerRef: React.RefObject<HTMLDivElement | null>,
): ResponsiveGridLayout {
  const [layout, setLayout] = useState<ResponsiveGridLayout>({
    columnCount: 1,
    cardWidth: 160,
    gap: 24, // matches gap-6 (1.5rem)
  });

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    let resizeObserver: ResizeObserver | null = null;
    let frameId: number | null = null;

    const computeLayout = () => {
      const container = containerRef.current;
      if (!container) {
        return;
      }

      const width = container.clientWidth || window.innerWidth || 0;

      // Approximate Tailwind breakpoints:
      // - base:  min 140px width, gap-6
      // - md:    min 160px width, gap-8
      // - lg+:   min 180px width, gap-8
      let minCardWidth = 140;
      let gap = 24; // 1.5rem

      if (width >= 1024) {
        minCardWidth = 180;
        gap = 32; // 2rem
      } else if (width >= 768) {
        minCardWidth = 160;
        gap = 32;
      }

      const availableWidth = Math.max(width, minCardWidth);
      const estimatedColumns = Math.max(
        1,
        Math.floor((availableWidth + gap) / (minCardWidth + gap)),
      );

      // Distribute cards evenly across the row so they perfectly fill
      // the available width while keeping the configured gaps.
      const rawCardWidth =
        (availableWidth - gap * (estimatedColumns - 1)) / estimatedColumns;
      const cardWidth = Math.max(rawCardWidth, minCardWidth);

      setLayout({
        columnCount: estimatedColumns,
        cardWidth,
        gap,
      });
    };

    const setupWhenReady = () => {
      const container = containerRef.current;
      if (!container) {
        frameId = window.requestAnimationFrame(setupWhenReady);
        return;
      }

      computeLayout();

      if (typeof ResizeObserver !== "undefined") {
        resizeObserver = new ResizeObserver(() => {
          computeLayout();
        });
        resizeObserver.observe(container);
      }

      window.addEventListener("resize", computeLayout);
      window.addEventListener("orientationchange", computeLayout);
    };

    setupWhenReady();

    return () => {
      if (frameId !== null) {
        window.cancelAnimationFrame(frameId);
      }
      window.removeEventListener("resize", computeLayout);
      window.removeEventListener("orientationchange", computeLayout);
      resizeObserver?.disconnect();
    };
  }, [containerRef]);

  return layout;
}
