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

import {
  forwardRef,
  useCallback,
  useImperativeHandle,
  useMemo,
  useRef,
} from "react";
import { useCurrentPageTracker } from "@/hooks/reading/comic/useCurrentPageTracker";
import { useStepKeyboardNavigation } from "@/hooks/reading/comic/useStepKeyboardNavigation";
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
 * - SRP: Focuses on orchestration (config + keyboard navigation + ref forwarding)
 * - OCP: Configurable via props, extensible without modification
 * - DIP: Depends on abstractions (hooks) not concrete implementations
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
  const { config, initialPage, onPageChange, totalPages, ...restProps } = props;
  const innerRef = useRef<VirtualizedComicViewHandle | null>(null);

  // Extract page tracking to separate hook (SRP)
  const initialPageClamped = Math.max(
    1,
    Math.min(initialPage ?? 1, totalPages),
  );
  const pageTracker = useCurrentPageTracker(initialPageClamped);

  // Create page change handler that updates tracker and calls parent callback
  const handlePageChange = useMemo(
    () => pageTracker.createPageChangeHandler(onPageChange),
    [pageTracker, onPageChange],
  );

  // Navigation callback for keyboard hook
  const goToPage = useCallback((page: number) => {
    innerRef.current?.scrollToPage(page, "smooth");
  }, []);

  // Set up keyboard navigation (DIP: depends on hook abstraction)
  useStepKeyboardNavigation({
    readingDirection: "vertical",
    totalPages,
    getCurrentPage: pageTracker.getCurrentPage,
    onGoToPage: goToPage,
  });

  // Forward imperative handle (ISP: exposes full interface)
  useImperativeHandle(
    ref,
    () => ({
      jumpToPage: (page: number) => innerRef.current?.jumpToPage(page),
      jumpToProgress: (progress: number) =>
        innerRef.current?.jumpToProgress(progress),
      scrollToPage: (page: number, behavior?: ScrollBehavior) =>
        innerRef.current?.scrollToPage(page, behavior),
    }),
    [],
  );

  const mergedConfig: VirtualizedViewConfig = {
    ...CONTINUOUS_CONFIG,
    ...config,
  };

  return (
    <BaseVirtualizedComicView
      ref={innerRef}
      {...restProps}
      totalPages={totalPages}
      onPageChange={handlePageChange}
      config={mergedConfig}
      initialPage={initialPage}
    />
  );
});

ContinuousComicView.displayName = "ContinuousComicView";
