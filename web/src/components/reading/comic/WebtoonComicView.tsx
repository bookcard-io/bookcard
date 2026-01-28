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
 * Mode wrapper around BaseVirtualizedComicView with webtoon-specific defaults.
 *
 * Notes
 * -----
 * This component orchestrates:
 * - Mode defaults (webtoon config)
 * - Page tracking (for input-driven navigation)
 * - Keyboard navigation (vertical strategy)
 *
 * Rendering and virtualization are delegated to `BaseVirtualizedComicView`.
 *
 * This refactored version follows:
 * - DRY: Reuses BaseVirtualizedComicView instead of duplicating code
 * - SRP: Focuses on orchestration, delegates rendering to base component
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
  const { config, initialPage, onPageChange, totalPages, ...restProps } = props;
  const innerRef = useRef<VirtualizedComicViewHandle | null>(null);

  const initialPageClamped = Math.max(
    1,
    Math.min(initialPage ?? 1, totalPages),
  );
  const pageTracker = useCurrentPageTracker(initialPageClamped);

  const handlePageChange = useMemo(
    () => pageTracker.createPageChangeHandler(onPageChange),
    [pageTracker, onPageChange],
  );

  const goToPage = useCallback((page: number) => {
    innerRef.current?.scrollToPage(page, "smooth");
  }, []);

  useStepKeyboardNavigation({
    readingDirection: "vertical",
    totalPages,
    getCurrentPage: pageTracker.getCurrentPage,
    onGoToPage: goToPage,
  });

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
    ...WEBTOON_CONFIG,
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

WebtoonComicView.displayName = "WebtoonComicView";
