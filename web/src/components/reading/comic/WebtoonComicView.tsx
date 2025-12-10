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

import { forwardRef } from "react";
import {
  BaseVirtualizedComicView,
  type BaseVirtualizedComicViewProps,
  type VirtualizedComicViewHandle,
  type VirtualizedViewConfig,
  WEBTOON_CONFIG,
} from "./BaseVirtualizedComicView";

export interface WebtoonComicViewProps
  extends Omit<BaseVirtualizedComicViewProps, "config"> {
  config?: Partial<VirtualizedViewConfig>;
  /** Initial page number to jump to on load (1-based) */
  initialPage?: number | null;
}

export interface WebtoonComicViewHandle extends VirtualizedComicViewHandle {}

/**
 * Webtoon-style comic view with smooth infinite scrolling.
 *
 * Thin wrapper around BaseVirtualizedComicView with webtoon-specific defaults.
 * Displays comic pages in an infinite vertical scroll.
 * Pages are loaded as the user scrolls down.
 *
 * This refactored version follows:
 * - DRY: Reuses BaseVirtualizedComicView instead of duplicating code
 * - SRP: Focuses solely on configuration, delegates rendering to base component
 * - OCP: Configurable via props, extensible without modification
 * - Consistency: Uses useVisiblePage hook like ContinuousComicView
 *
 * Parameters
 * ----------
 * props : WebtoonComicViewProps
 *     Component props including book data, callbacks, and optional config overrides.
 * ref : WebtoonComicViewHandle
 *     Imperative handle for programmatic navigation.
 */
export const WebtoonComicView = forwardRef<
  WebtoonComicViewHandle,
  WebtoonComicViewProps
>((props, ref) => {
  const { config, initialPage, ...restProps } = props;
  const mergedConfig: VirtualizedViewConfig = {
    ...WEBTOON_CONFIG,
    ...config,
  };

  return (
    <BaseVirtualizedComicView
      ref={ref}
      {...restProps}
      config={mergedConfig}
      initialPage={initialPage}
    />
  );
});

WebtoonComicView.displayName = "WebtoonComicView";
