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

export interface UseStickyStatusOptions {
  /** Distance in pixels to fade the background opacity (default: 100). */
  fadeDistance?: number;
  /** Scroll container selector (default: '[data-page-scroll-container="true"]'). */
  scrollContainerSelector?: string;
}

export interface UseStickyStatusResult {
  /** Ref to attach to the status element. */
  statusRef: React.RefObject<HTMLDivElement | null>;
  /** Whether the status should be sticky. */
  isSticky: boolean;
  /** Background opacity (0-1). */
  opacity: number;
}

/**
 * Hook for managing sticky status bar with opacity transitions.
 *
 * Tracks scroll position relative to the status element and manages sticky
 * positioning with background opacity fade. Follows SRP by handling only
 * scroll-based sticky behavior logic. Follows IOC by accepting configurable options.
 *
 * Parameters
 * ----------
 * options : UseStickyStatusOptions
 *     Configuration options for sticky behavior.
 *
 * Returns
 * -------
 * UseStickyStatusResult
 *     Object containing statusRef, isSticky state, and opacity value.
 */
export function useStickyStatus(
  options: UseStickyStatusOptions = {},
): UseStickyStatusResult {
  const {
    fadeDistance = 100,
    scrollContainerSelector = '[data-page-scroll-container="true"]',
  } = options;
  const statusRef = useRef<HTMLDivElement | null>(null);
  const [isSticky, setIsSticky] = useState(false);
  const [opacity, setOpacity] = useState(0);
  const lastScrollTopRef = useRef<number>(0);
  const isStickyRef = useRef<boolean>(false);
  const originalOffsetTopRef = useRef<number | null>(null);
  const currentOpacityRef = useRef<number>(0);
  const rafIdRef = useRef<number | null>(null);

  useEffect(() => {
    const statusElement = statusRef.current;
    if (!statusElement) {
      return;
    }

    const scrollContainer =
      typeof document !== "undefined"
        ? (document.querySelector(
            scrollContainerSelector,
          ) as HTMLElement | null)
        : null;

    if (!scrollContainer) {
      return;
    }

    const handleScroll = () => {
      // Cancel any pending animation frame
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
      }

      // Use requestAnimationFrame to batch updates and prevent jitter
      rafIdRef.current = requestAnimationFrame(() => {
        const scrollTop = scrollContainer.scrollTop;
        const scrollDirection =
          scrollTop > lastScrollTopRef.current ? "down" : "up";
        lastScrollTopRef.current = scrollTop;

        // If we're already sticky, use the stored original position
        if (isStickyRef.current && originalOffsetTopRef.current !== null) {
          const scrollPastOriginal = scrollTop - originalOffsetTopRef.current;

          if (scrollPastOriginal > 0) {
            // Still scrolled past - calculate opacity
            // Opacity reaches 100% in half the fadeDistance for faster transition
            const effectiveFadeDistance = fadeDistance / 1.25;
            let calculatedOpacity = Math.min(
              1,
              scrollPastOriginal / effectiveFadeDistance,
            );

            // If scrolling up and close to original position, fade out
            if (
              scrollDirection === "up" &&
              scrollPastOriginal <= effectiveFadeDistance
            ) {
              calculatedOpacity = Math.max(
                0,
                scrollPastOriginal / effectiveFadeDistance,
              );
            }

            currentOpacityRef.current = calculatedOpacity;
            setOpacity(calculatedOpacity);
          } else {
            // Scrolled back to or above original position - unstick
            setIsSticky(false);
            isStickyRef.current = false;
            originalOffsetTopRef.current = null;
            currentOpacityRef.current = 0;
            setOpacity(0);
          }
          return;
        }

        // Not sticky yet - check if we should become sticky
        const statusRect = statusElement.getBoundingClientRect();
        const containerRect = scrollContainer.getBoundingClientRect();

        // Calculate the status element's position relative to the scroll container
        const statusTopRelative = statusRect.top - containerRect.top;

        // Check if status element has been scrolled past (top of status is above viewport top)
        if (statusTopRelative <= 0) {
          // Element has been scrolled past - make it sticky
          if (!isStickyRef.current) {
            // Store the original offsetTop (position in document flow) before making it sticky
            // This is the scroll position where the element's top would be at the container's top
            originalOffsetTopRef.current = scrollTop + statusTopRelative;

            setIsSticky(true);
            isStickyRef.current = true;
          }

          // Calculate opacity based on how far we've scrolled past the element
          // Opacity reaches 100% in half the fadeDistance for faster transition
          const scrollPastDistance = Math.abs(statusTopRelative);
          const effectiveFadeDistance = fadeDistance / 2;
          const calculatedOpacity = Math.min(
            1,
            scrollPastDistance / effectiveFadeDistance,
          );
          currentOpacityRef.current = calculatedOpacity;
          setOpacity(calculatedOpacity);
        } else {
          // Status element is still visible - not sticky.
          // Opacity is already guaranteed to be 0 in this branch, so no update
          // is necessary. This avoids unnecessary re-renders.
        }
      });
    };

    // Initial check
    handleScroll();

    scrollContainer.addEventListener("scroll", handleScroll, { passive: true });
    // Also listen to resize to recalculate on layout changes
    window.addEventListener("resize", handleScroll, { passive: true });

    return () => {
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
      scrollContainer.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleScroll);
    };
  }, [fadeDistance, scrollContainerSelector]);

  return { statusRef, isSticky, opacity };
}
