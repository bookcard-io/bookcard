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

import type { ComicReadingDirection } from "./comicReader";
import type { KeydownEventTarget } from "./eventTargets";

/**
 * Common types for paged navigation inputs (keyboard / touch / click).
 *
 * Notes
 * -----
 * These types are UI-framework-agnostic. React (or any other framework)
 * should adapt its concrete event objects into these abstractions.
 */

/** Canonical navigation actions for a paged reader. */
export type PagedNavigationAction =
  | "next"
  | "previous"
  | "first"
  | "last"
  | null;

/** Minimal callbacks for forward/backward navigation (ISP-friendly). */
export interface BasicNavigationCallbacks {
  canGoNext: boolean;
  canGoPrevious: boolean;
  onNext: () => void;
  onPrevious: () => void;
}

/** Optional callbacks for jumping to specific pages (keyboard Home/End). */
export interface PageJumpCallbacks {
  totalPages: number;
  onGoToPage: (page: number) => void;
}

/** Strategy for mapping different inputs to navigation actions (OCP). */
export interface PagedNavigationStrategy {
  readonly readingDirection: ComicReadingDirection;

  mapKeyToAction: (key: string) => PagedNavigationAction;
  mapSwipeToAction: (
    deltaX: number,
    deltaY: number,
    thresholdPx: number,
  ) => PagedNavigationAction;
  mapWheelToAction: (
    deltaX: number,
    deltaY: number,
    thresholdPx: number,
  ) => PagedNavigationAction;
  mapClickToAction: (
    relativeX: number,
    relativeY: number,
  ) => PagedNavigationAction;
}

export type { KeydownEventTarget };
