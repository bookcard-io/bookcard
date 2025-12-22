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
import type {
  FontFamily,
  PageColor,
} from "@/components/reading/ReadingThemeSettings";
import { calculateProgressFromCfi } from "@/utils/epubLocation";
import {
  applyThemeToRendition,
  createContentHook,
} from "@/utils/epubRendering";

/**
 * EPUB rendition setup utilities.
 *
 * Centralized utilities for setting up EPUB.js renditions with themes,
 * content hooks, and location generation. Follows SRP by separating
 * setup logic from UI components.
 */

/**
 * Options for setting up a rendition.
 */
export interface RenditionSetupOptions {
  /** The rendition instance to set up. */
  rendition: Rendition;
  /** Ref to store the book instance. */
  bookRef: RefObject<Book | null>;
  /** Initial CFI location to apply. */
  initialCfi?: string | null;
  /** Function to apply initial CFI. */
  applyInitialCfi?: () => void;
  /** Initial page color theme. */
  pageColor: PageColor;
  /** Initial font family. */
  fontFamily: FontFamily;
  /** Initial font size in pixels. */
  fontSize: number;
  /** Ref to current page color theme. */
  pageColorRef: RefObject<PageColor>;
  /** Ref to current font family. */
  fontFamilyRef: RefObject<FontFamily>;
  /** Ref to current font size. */
  fontSizeRef: RefObject<number>;
  /** Callback when locations are ready. */
  onLocationsReadyChange?: (ready: boolean) => void;
  /** Callback when location changes. */
  onLocationChange?: (
    cfi: string,
    progress: number,
    skipBackendUpdate?: boolean,
  ) => void;
  /** Ref indicating if initial load is in progress. */
  isInitialLoadRef: RefObject<boolean>;
}

/**
 * Set up an EPUB.js rendition with themes, content hooks, and location generation.
 *
 * Parameters
 * ----------
 * options : RenditionSetupOptions
 *     Configuration for rendition setup.
 */
export function setupRendition(options: RenditionSetupOptions): void {
  const {
    rendition,
    bookRef,
    initialCfi,
    applyInitialCfi,
    pageColor,
    fontFamily,
    fontSize,
    pageColorRef,
    fontFamilyRef,
    fontSizeRef,
    onLocationsReadyChange,
    onLocationChange,
    isInitialLoadRef,
  } = options;

  // Store book reference
  bookRef.current = rendition.book;

  // Apply initial CFI if provided
  if (applyInitialCfi) {
    applyInitialCfi();
  }

  // Apply initial theme
  applyThemeToRendition(rendition, pageColor, fontFamily, fontSize);

  // Monkey patch display to catch errors and prevent unhandled rejections
  const originalDisplay = rendition.display;
  // biome-ignore lint/suspicious/noExplicitAny: Monkey-patching Rendition.display requires any due to epubjs type limitations
  (rendition as any).display = function (target?: string) {
    // biome-ignore lint/suspicious/noExplicitAny: originalDisplay.call requires any due to epubjs type limitations
    return (originalDisplay as any).call(this, target).catch((err: unknown) => {
      console.warn("Rendition display error (recovered):", err);
      // Swallow error to prevent unhandled rejection crashing the app
      // This allows the UI to remain responsive (e.g. TOC navigation)
      return Promise.resolve();
    });
  };

  // Monkey patch next/prev to debug navigation issues and fallback if stuck
  const originalNext = rendition.next;
  rendition.next = function () {
    // biome-ignore lint/suspicious/noExplicitAny: internal property access
    const currentLocation = (rendition as any).currentLocation();

    return originalNext.call(this).then(() => {
      // biome-ignore lint/suspicious/noExplicitAny: internal property access
      const newLocation = (rendition as any).currentLocation();
      if (
        currentLocation &&
        newLocation &&
        currentLocation.start.cfi === newLocation.start.cfi
      ) {
        // Attempt to find the next linear spine item
        try {
          // biome-ignore lint/suspicious/noExplicitAny: internal property access
          const book = (rendition as any).book;
          const currentSpineIndex = currentLocation.start.index;
          const spine = book.spine;

          const nextIndex = currentSpineIndex + 1;
          const nextSection = spine.get(nextIndex);

          // Skip non-linear items if possible, though specific books might need them
          // For now, just try the immediate next item to unblock
          if (nextSection) {
            return rendition.display(nextSection.href);
          }
        } catch (e) {
          console.error("Error during manual spine navigation fallback:", e);
        }
      }
      return Promise.resolve();
    });
  };

  const originalPrev = rendition.prev;
  rendition.prev = function () {
    return originalPrev.call(this);
  };

  // Register content hook to ensure styles are applied to all pages
  const contentHook = createContentHook(
    rendition,
    pageColorRef,
    fontFamilyRef,
    fontSizeRef,
  );
  rendition.hooks.content.register(contentHook);

  // Generate locations and notify when ready
  handleLocationGeneration({
    book: bookRef.current,
    initialCfi,
    onLocationsReadyChange,
    onLocationChange,
    isInitialLoadRef,
  });
}

/**
 * Options for handling location generation.
 */
interface LocationGenerationOptions {
  /** The book instance. */
  book: Book | null;
  /** Initial CFI location. */
  initialCfi?: string | null;
  /** Callback when locations are ready. */
  onLocationsReadyChange?: (ready: boolean) => void;
  /** Callback when location changes. */
  onLocationChange?: (
    cfi: string,
    progress: number,
    skipBackendUpdate?: boolean,
  ) => void;
  /** Ref indicating if initial load is in progress. */
  isInitialLoadRef: RefObject<boolean>;
}

/**
 * Handle EPUB location generation and notify when ready.
 *
 * Parameters
 * ----------
 * options : LocationGenerationOptions
 *     Configuration for location generation handling.
 */
function handleLocationGeneration(options: LocationGenerationOptions): void {
  const {
    book,
    initialCfi,
    onLocationsReadyChange,
    onLocationChange,
    isInitialLoadRef,
  } = options;

  const markInitialLoadComplete = () => {
    setTimeout(() => {
      isInitialLoadRef.current = false;
    }, 500);
  };

  if (book?.locations && onLocationsReadyChange) {
    book.locations
      .generate(200)
      .then(() => {
        onLocationsReadyChange(true);

        // If we have an initial CFI, calculate progress from it now that locations are ready
        if (initialCfi && onLocationChange) {
          try {
            const calculatedProgress = calculateProgressFromCfi(
              book,
              initialCfi,
            );
            // Update with calculated progress, but skip backend update (initial load)
            onLocationChange(initialCfi, calculatedProgress, true);
          } catch (error) {
            console.warn("Error calculating initial progress from CFI:", error);
          }
        }

        markInitialLoadComplete();
      })
      .catch((error) => {
        console.error("Error generating locations:", error);
        // Mark ready anyway so UI doesn't stay locked
        onLocationsReadyChange(true);
        markInitialLoadComplete();
      });
  } else if (onLocationsReadyChange) {
    onLocationsReadyChange(false);
    markInitialLoadComplete();
  } else {
    markInitialLoadComplete();
  }
}
