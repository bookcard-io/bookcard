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

export interface UseSidebarScrollOptions {
  /** Delay in milliseconds before hiding scrollbar after scrolling stops (default: 1000). */
  hideDelay?: number;
}

export interface UseSidebarScrollResult {
  /** Ref to attach to the scrollable element. */
  navRef: React.RefObject<HTMLElement | null>;
  /** Whether the element is currently scrolling. */
  isScrolling: boolean;
}

/**
 * Hook for managing sidebar scroll behavior.
 *
 * Tracks scroll state and shows/hides scrollbar based on scroll activity.
 * Follows SRP by handling only scroll behavior logic.
 * Follows IOC by accepting configurable options.
 *
 * Parameters
 * ----------
 * options : UseSidebarScrollOptions
 *     Configuration options for scroll behavior.
 *
 * Returns
 * -------
 * UseSidebarScrollResult
 *     Object containing navRef and isScrolling state.
 */
export function useSidebarScroll(
  options: UseSidebarScrollOptions = {},
): UseSidebarScrollResult {
  const { hideDelay = 1000 } = options;
  const [isScrolling, setIsScrolling] = useState(false);
  const navRef = useRef<HTMLElement>(null);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleScroll = useCallback(() => {
    setIsScrolling(true);
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }
    scrollTimeoutRef.current = setTimeout(() => {
      setIsScrolling(false);
    }, hideDelay);
  }, [hideDelay]);

  useEffect(() => {
    const navElement = navRef.current;
    if (!navElement) {
      return;
    }

    navElement.addEventListener("scroll", handleScroll);
    return () => {
      navElement.removeEventListener("scroll", handleScroll);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [handleScroll]);

  return { navRef, isScrolling };
}
