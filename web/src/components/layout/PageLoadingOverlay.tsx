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

import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useGlobalPageLoadingSignals } from "@/hooks/useGlobalPageLoadingSignals";
import { cn } from "@/libs/utils";

/**
 * Global page loading overlay component.
 *
 * Displays a soft, centered spinner over the main content area whenever
 * high‑level application state is loading or a navigation is in progress.
 * The overlay is controlled entirely at the layout level – child components
 * do not need to report or manage their own loading state.
 *
 * Loading signals are aggregated via `useGlobalPageLoadingSignals` to keep
 * this component focused purely on overlay behavior and animation rather than
 * individual data sources.
 */
export function PageLoadingOverlay() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [isNavTransition, setIsNavTransition] = useState(false);
  const [isVisible, setIsVisible] = useState(false);

  const lastLocationKeyRef = useRef<string | null>(null);
  const navTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const showDelayTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const hideTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const visibleSinceRef = useRef<number | null>(null);

  // Combine all loading signals into a single boolean via dedicated hook
  const isLogicalLoading = useGlobalPageLoadingSignals(isNavTransition);

  // Detect navigation (including query param changes such as ?tab=...)
  useEffect(() => {
    const search = searchParams?.toString() ?? "";
    const currentKey = `${pathname}?${search}`;

    // Initialize on first render
    if (lastLocationKeyRef.current === null) {
      lastLocationKeyRef.current = currentKey;
      return;
    }

    if (lastLocationKeyRef.current !== currentKey) {
      lastLocationKeyRef.current = currentKey;
      setIsNavTransition(true);

      if (navTimeoutRef.current) {
        clearTimeout(navTimeoutRef.current);
      }

      // Keep the navigation flag on briefly to allow the overlay
      // to respond even if underlying data loads very quickly.
      const NAV_TRANSITION_MS = 300;
      navTimeoutRef.current = setTimeout(() => {
        setIsNavTransition(false);
      }, NAV_TRANSITION_MS);
    }
  }, [pathname, searchParams]);

  // Control overlay visibility with debounce and minimum display duration
  useEffect(() => {
    const SHOW_DELAY_MS = 80;
    const MIN_VISIBLE_MS = 220;

    // Helper to clear timers
    const clearTimers = () => {
      if (showDelayTimeoutRef.current) {
        clearTimeout(showDelayTimeoutRef.current);
        showDelayTimeoutRef.current = null;
      }
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current);
        hideTimeoutRef.current = null;
      }
    };

    if (isLogicalLoading) {
      // Cancel any pending hide, we are loading again
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current);
        hideTimeoutRef.current = null;
      }

      // If already visible, nothing else to do
      if (isVisible) {
        return;
      }

      // Delay appearance slightly to avoid flicker on ultra‑fast operations
      if (showDelayTimeoutRef.current) {
        clearTimeout(showDelayTimeoutRef.current);
      }
      showDelayTimeoutRef.current = setTimeout(() => {
        visibleSinceRef.current = Date.now();
        setIsVisible(true);
      }, SHOW_DELAY_MS);

      return () => {
        clearTimers();
      };
    }

    // Not logically loading anymore: ensure we keep the overlay on
    // for a short minimum period to allow a smooth fade‑out.
    if (!isVisible) {
      clearTimers();
      return;
    }

    if (showDelayTimeoutRef.current) {
      clearTimeout(showDelayTimeoutRef.current);
      showDelayTimeoutRef.current = null;
    }

    const now = Date.now();
    const elapsed = visibleSinceRef.current
      ? now - visibleSinceRef.current
      : MIN_VISIBLE_MS;
    const remaining = elapsed >= MIN_VISIBLE_MS ? 0 : MIN_VISIBLE_MS - elapsed;

    hideTimeoutRef.current = setTimeout(() => {
      visibleSinceRef.current = null;
      setIsVisible(false);
    }, remaining);

    return () => {
      clearTimers();
    };
  }, [isLogicalLoading, isVisible]);

  // Ensure timers are cleared on unmount
  useEffect(
    () => () => {
      if (navTimeoutRef.current) {
        clearTimeout(navTimeoutRef.current);
      }
      if (showDelayTimeoutRef.current) {
        clearTimeout(showDelayTimeoutRef.current);
      }
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current);
      }
    },
    [],
  );

  return (
    <div
      className={cn(
        "pointer-events-none absolute inset-0 z-[900] flex items-center justify-center transition-[opacity,visibility] duration-300 ease-out",
        isVisible ? "visible opacity-100" : "invisible opacity-0",
      )}
      aria-hidden={!isVisible}
    >
      <div
        className="rounded-full shadow-md"
        style={{
          padding: "1rem",
          backgroundColor:
            "color-mix(in srgb, var(--color-surface-a10) 70%, transparent)",
          boxShadow: "0 4px 10px rgba(0, 0, 0, 0.3)",
        }}
      >
        <i
          className="pi pi-spin pi-spinner text-[var(--color-primary-a0)]"
          style={{ fontSize: "1.75rem" }}
          aria-hidden="true"
        />
      </div>
    </div>
  );
}
