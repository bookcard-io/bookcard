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

import type { VirtualItem } from "@tanstack/react-virtual";
import { type RefObject, useEffect, useState } from "react";

/**
 * Hook to determine the current visible page based on viewport center.
 *
 * @param containerRef Ref to the scroll container
 * @param virtualItems List of currently virtualized items
 * @returns The page number (1-based) closest to the center of the viewport
 */
export function useVisiblePage(
  containerRef: RefObject<HTMLDivElement | null>,
  virtualItems: VirtualItem[],
): number {
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    if (!containerRef.current || virtualItems.length === 0) return;

    const container = containerRef.current;
    // We calculate the center point of the viewport relative to the scroll content
    const viewportCenter = container.scrollTop + container.clientHeight / 2;

    const closest = virtualItems.reduce(
      (best, item) => {
        const itemCenter = (item.start + item.end) / 2;
        const distance = Math.abs(viewportCenter - itemCenter);
        return distance < best.distance
          ? { page: item.index + 1, distance }
          : best;
      },
      { page: 1, distance: Infinity },
    );

    if (closest.page !== currentPage) {
      setCurrentPage(closest.page);
    }
  }, [virtualItems, currentPage, containerRef.current]); // Intentionally removed containerRef from deps

  return currentPage;
}
