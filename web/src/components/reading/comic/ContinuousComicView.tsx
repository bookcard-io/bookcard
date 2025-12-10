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
  CONTINUOUS_CONFIG,
  type VirtualizedComicViewHandle,
  type VirtualizedViewConfig,
} from "./BaseVirtualizedComicView";

export interface ContinuousComicViewProps
  extends Omit<BaseVirtualizedComicViewProps, "config"> {
  config?: Partial<VirtualizedViewConfig>;
  /** Initial page number to jump to on load (1-based) */
  initialPage?: number | null;
}

export interface ContinuousComicViewHandle extends VirtualizedComicViewHandle {}

/**
 * Continuous comic view with page snapping.
 *
 * Thin wrapper around BaseVirtualizedComicView with continuous-specific defaults.
 * Displays comic pages in a vertical scroll with page snapping.
 * Users can scroll continuously through all pages.
 *
 * This refactored version follows:
 * - DRY: Reuses BaseVirtualizedComicView instead of duplicating code
 * - SRP: Focuses solely on configuration, delegates rendering to base component
 * - OCP: Configurable via props, extensible without modification
 *
 * Parameters
 * ----------
 * props : ContinuousComicViewProps
 *     Component props including book data, callbacks, and optional config overrides.
 * ref : ContinuousComicViewHandle
 *     Imperative handle for programmatic navigation.
 */
export const ContinuousComicView = forwardRef<
  ContinuousComicViewHandle,
  ContinuousComicViewProps
>((props, ref) => {
  const { config, initialPage, ...restProps } = props;
  const mergedConfig: VirtualizedViewConfig = {
    ...CONTINUOUS_CONFIG,
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

ContinuousComicView.displayName = "ContinuousComicView";
