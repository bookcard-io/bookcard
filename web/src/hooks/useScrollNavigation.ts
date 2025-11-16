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

import { useCallback, useEffect, useRef, useState } from "react";
import { scrollContainerTo } from "@/utils/scroll";

export interface UseScrollNavigationOptions {
  /** Scroll container selector (default: '[data-page-scroll-container="true"]'). */
  scrollContainerSelector?: string;
  /** Base scroll amount in pixels (default: 325). */
  scrollAmount?: number;
}

export interface UseScrollNavigationResult {
  /** Handler to scroll to the top of the container. */
  scrollToTop: () => void;
  /** Handler to scroll up progressively. */
  scrollUp: () => void;
  /** Handler to scroll down progressively. */
  scrollDown: () => void;
}

/**
 * Hook for managing progressive scroll navigation.
 *
 * Provides handlers for scrolling to top, up, and down with progressive
 * scroll amounts. Tracks scroll direction to reset counters appropriately.
 * Follows SRP by handling only scroll navigation logic.
 * Follows IOC by accepting configurable options.
 *
 * Parameters
 * ----------
 * options : UseScrollNavigationOptions
 *     Configuration options for scroll navigation.
 *
 * Returns
 * -------
 * UseScrollNavigationResult
 *     Object containing scroll handlers.
 */
export function useScrollNavigation(
  options: UseScrollNavigationOptions = {},
): UseScrollNavigationResult {
  const {
    scrollContainerSelector = '[data-page-scroll-container="true"]',
    scrollAmount = 325,
  } = options;

  const scrollUpCountRef = useRef<number>(0);
  const scrollDownCountRef = useRef<number>(0);
  const lastScrollTopRef = useRef<number>(0);
  const [scrollContainer, setScrollContainer] = useState<HTMLElement | null>(
    null,
  );

  // Initialize scroll container
  useEffect(() => {
    const container =
      typeof document !== "undefined"
        ? (document.querySelector(
            scrollContainerSelector,
          ) as HTMLElement | null)
        : null;
    setScrollContainer(container);
    if (container) {
      lastScrollTopRef.current = container.scrollTop;
    }
  }, [scrollContainerSelector]);

  // Track scroll direction and reset counters when scrolling in opposite direction
  useEffect(() => {
    if (!scrollContainer) {
      return;
    }

    const handleScroll = () => {
      const currentScrollTop = scrollContainer.scrollTop;
      const scrollDirection =
        currentScrollTop < lastScrollTopRef.current ? "up" : "down";

      // Reset counters when scrolling in opposite direction
      if (scrollDirection === "up") {
        scrollDownCountRef.current = 0;
      } else {
        scrollUpCountRef.current = 0;
      }

      lastScrollTopRef.current = currentScrollTop;
    };

    scrollContainer.addEventListener("scroll", handleScroll, { passive: true });
    return () => {
      scrollContainer.removeEventListener("scroll", handleScroll);
    };
  }, [scrollContainer]);

  const scrollToTop = useCallback(() => {
    if (!scrollContainer) {
      return;
    }
    scrollContainerTo(scrollContainer, 0, "smooth");
    scrollUpCountRef.current = 0;
    scrollDownCountRef.current = 0;
  }, [scrollContainer]);

  const scrollUp = useCallback(() => {
    if (!scrollContainer) {
      return;
    }
    scrollUpCountRef.current += 1;
    const scrollDistance = scrollAmount * scrollUpCountRef.current;
    const newScrollTop = Math.max(
      0,
      scrollContainer.scrollTop - scrollDistance,
    );
    scrollContainerTo(scrollContainer, newScrollTop, "smooth");
  }, [scrollContainer, scrollAmount]);

  const scrollDown = useCallback(() => {
    if (!scrollContainer) {
      return;
    }
    scrollDownCountRef.current += 1;
    const scrollDistance = scrollAmount * scrollDownCountRef.current;
    const newScrollTop = scrollContainer.scrollTop + scrollDistance;
    scrollContainerTo(scrollContainer, newScrollTop, "smooth");
  }, [scrollContainer, scrollAmount]);

  return {
    scrollToTop,
    scrollUp,
    scrollDown,
  };
}
