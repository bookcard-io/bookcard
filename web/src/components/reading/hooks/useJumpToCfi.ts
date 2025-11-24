// Copyright (C) 2025 khoa and others
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

import type { Book, Rendition } from "epubjs";
import type { RefObject } from "react";
import { useEffect } from "react";
import { calculateProgressFromCfi } from "@/utils/epubLocation";

/**
 * Options for useJumpToCfi hook.
 */
export interface UseJumpToCfiOptions {
  /** Ref to rendition instance. */
  renditionRef: RefObject<Rendition | undefined>;
  /** Ref to book instance. */
  bookRef: RefObject<Book | null>;
  /** Ref indicating if navigation is in progress. */
  isNavigatingRef: RefObject<boolean>;
  /** Function to set location. */
  setLocation: (location: string) => void;
  /** Callback when location changes. */
  onLocationChange?: (
    cfi: string,
    progress: number,
    skipBackendUpdate?: boolean,
  ) => void;
  /** Callback to register jump to CFI handler. */
  onJumpToCfi?: (handler: ((cfi: string) => void) | null) => void;
}

/**
 * Hook to register jump to CFI handler.
 *
 * Creates a handler that navigates to a specific CFI location.
 * Follows SRP by focusing solely on CFI navigation.
 * Follows IOC by accepting dependencies as parameters.
 *
 * Parameters
 * ----------
 * options : UseJumpToCfiOptions
 *     Hook options including refs and callbacks.
 */
export function useJumpToCfi({
  renditionRef,
  bookRef,
  isNavigatingRef,
  setLocation,
  onLocationChange,
  onJumpToCfi,
}: UseJumpToCfiOptions): void {
  useEffect(() => {
    if (!onJumpToCfi) {
      return;
    }

    const jumpToCfiHandler = (cfi: string) => {
      const rendition = renditionRef.current;
      const book = bookRef.current;

      if (!rendition) {
        // eslint-disable-next-line no-console
        console.warn("Cannot jump to CFI: rendition not ready");
        return;
      }

      if (!book) {
        // eslint-disable-next-line no-console
        console.warn("Cannot jump to CFI: book not ready");
        return;
      }

      // Mark that we're programmatically navigating to prevent location callback from interfering
      isNavigatingRef.current = true;

      try {
        rendition.display(cfi);
        // Update location state to match
        setLocation(cfi);

        // Trigger location change callback with CFI and progress
        if (onLocationChange) {
          const actualProgress = calculateProgressFromCfi(book, cfi);
          onLocationChange(
            cfi,
            actualProgress,
            false, // Don't skip backend update - this is a user action
          );
        }
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error("Error jumping to CFI:", error);
      } finally {
        // Reset flag after navigation completes
        setTimeout(() => {
          isNavigatingRef.current = false;
        }, 200);
      }
    };

    onJumpToCfi(jumpToCfiHandler);
    return () => {
      onJumpToCfi(null);
    };
  }, [
    onJumpToCfi,
    renditionRef,
    bookRef,
    setLocation,
    onLocationChange,
    isNavigatingRef,
  ]);
}
