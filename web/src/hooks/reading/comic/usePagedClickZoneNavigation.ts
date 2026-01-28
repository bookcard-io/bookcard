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

import { useCallback, useMemo } from "react";
import type { ComicReadingDirection } from "@/types/comicReader";
import type { BasicNavigationCallbacks } from "@/types/pagedNavigation";
import { getPagedNavigationStrategy } from "@/utils/pagedNavigation";

export interface ClickZoneHandlers {
  handleContainerClick: (e: React.MouseEvent<HTMLElement>) => void;
}

export interface PagedClickZoneNavigationOptions
  extends BasicNavigationCallbacks {
  containerRef: React.RefObject<HTMLElement | null>;
  readingDirection: ComicReadingDirection;
}

/**
 * Hook for handling click-zone navigation in the paged comic view.
 *
 * Parameters
 * ----------
 * options : PagedClickZoneNavigationOptions
 *     Container reference and navigation callbacks.
 *
 * Returns
 * -------
 * ClickZoneHandlers
 *     Click handler to attach to the container element.
 */
export function usePagedClickZoneNavigation({
  containerRef,
  readingDirection,
  canGoNext,
  canGoPrevious,
  onNext,
  onPrevious,
}: PagedClickZoneNavigationOptions): ClickZoneHandlers {
  const strategy = useMemo(
    () => getPagedNavigationStrategy(readingDirection),
    [readingDirection],
  );

  const handleContainerClick = useCallback(
    (e: React.MouseEvent<HTMLElement>) => {
      const el = containerRef.current;
      if (!el) return;

      const rect = el.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return;

      const relativeX = (e.clientX - rect.left) / rect.width;
      const relativeY = (e.clientY - rect.top) / rect.height;

      const action = strategy.mapClickToAction(relativeX, relativeY);
      if (action === "next" && canGoNext) onNext();
      else if (action === "previous" && canGoPrevious) onPrevious();
    },
    [containerRef, strategy, canGoNext, canGoPrevious, onNext, onPrevious],
  );

  return { handleContainerClick };
}
