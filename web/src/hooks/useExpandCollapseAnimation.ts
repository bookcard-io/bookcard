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

import { useEffect, useRef, useState } from "react";

export interface UseExpandCollapseAnimationOptions {
  /** Whether the item is currently expanded. */
  isExpanded: boolean;
  /** Animation duration in milliseconds (default: 500). */
  animationDuration?: number;
  /** Whether to scroll to the header when collapsing (default: true). */
  scrollOnCollapse?: boolean;
  /** Delay in milliseconds before scrolling when expanding (default: 0). */
  scrollDelay?: number;
}

export interface UseExpandCollapseAnimationResult {
  /** Whether the drawer content should be rendered. */
  shouldRender: boolean;
  /** Whether the animation is currently animating out (collapsing). */
  isAnimatingOut: boolean;
  /** Ref to attach to the container element for scrolling. */
  containerRef: React.RefObject<HTMLDivElement | null>;
}

/**
 * Hook for managing expand/collapse animation state.
 *
 * Handles animation state, scroll behavior, and cleanup.
 * Follows SRP by focusing solely on animation lifecycle.
 * Follows IOC by accepting configuration via options.
 *
 * Parameters
 * ----------
 * options : UseExpandCollapseAnimationOptions
 *     Configuration including expanded state and animation duration.
 *
 * Returns
 * -------
 * UseExpandCollapseAnimationResult
 *     Animation state and container ref.
 */
export function useExpandCollapseAnimation({
  isExpanded,
  animationDuration = 500,
  scrollOnCollapse = true,
  scrollDelay = 0,
}: UseExpandCollapseAnimationOptions): UseExpandCollapseAnimationResult {
  const [isAnimatingOut, setIsAnimatingOut] = useState(false);
  const [shouldRender, setShouldRender] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isExpanded) {
      setShouldRender(true);
      setIsAnimatingOut(false);
      // Scroll to header when expanding
      if (scrollDelay > 0) {
        const timer = setTimeout(() => {
          if (containerRef.current) {
            containerRef.current.scrollIntoView({
              behavior: "smooth",
              block: "start",
            });
          }
        }, scrollDelay);
        return () => clearTimeout(timer);
      }
      if (containerRef.current) {
        containerRef.current.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
      return undefined;
    }
    if (shouldRender) {
      setIsAnimatingOut(true);
      // Scroll to header when collapsing
      if (scrollOnCollapse && containerRef.current) {
        containerRef.current.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
      const timer = setTimeout(() => {
        setShouldRender(false);
        setIsAnimatingOut(false);
      }, animationDuration);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [
    isExpanded,
    shouldRender,
    animationDuration,
    scrollOnCollapse,
    scrollDelay,
  ]);

  return {
    shouldRender,
    isAnimatingOut,
    containerRef,
  };
}
