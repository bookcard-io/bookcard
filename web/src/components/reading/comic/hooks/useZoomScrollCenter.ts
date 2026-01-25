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

import type { RefObject } from "react";
import { useLayoutEffect, useRef } from "react";

export interface UseZoomScrollCenterOptions {
  containerRef: RefObject<HTMLElement | null>;
  zoomLevel: number;
}

/**
 * Keep the scroll viewport centered while zooming.
 *
 * Notes
 * -----
 * When zoom changes, the scroll offsets are adjusted so that the visual center
 * of the viewport remains stable. This isolates "view mechanics" from the main
 * rendering component (SOC/SRP).
 */
export function useZoomScrollCenter({
  containerRef,
  zoomLevel,
}: UseZoomScrollCenterOptions) {
  const prevZoomRef = useRef(zoomLevel);

  useLayoutEffect(() => {
    const el = containerRef.current;
    if (!el) {
      prevZoomRef.current = zoomLevel;
      return;
    }

    if (Math.abs(prevZoomRef.current - zoomLevel) <= 0.001) {
      return;
    }

    const ratio = zoomLevel / prevZoomRef.current;
    const { scrollLeft, scrollTop, clientWidth, clientHeight } = el;

    el.scrollLeft = (scrollLeft + clientWidth / 2) * ratio - clientWidth / 2;
    el.scrollTop = (scrollTop + clientHeight / 2) * ratio - clientHeight / 2;

    prevZoomRef.current = zoomLevel;
  }, [containerRef, zoomLevel]);
}
