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

import type { Rendition } from "epubjs";
import type { RefObject } from "react";
import { useCallback } from "react";
import type {
  FontFamily,
  PageColor,
} from "@/components/reading/ReadingThemeSettings";
import { setupRendition } from "@/utils/epubRenditionSetup";

/**
 * Options for creating rendition callback.
 */
export interface RenditionCallbackOptions {
  /** Ref to store the rendition instance. */
  renditionRef: RefObject<Rendition | undefined>;
  /** Ref to store the book instance. */
  bookRef: RefObject<import("epubjs").Book | null>;
  /** Initial CFI location to apply. */
  initialCfi?: string | null;
  /** Function to apply initial CFI. */
  applyInitialCfi?: () => void;
  /** Initial page color theme. */
  pageColor: PageColor;
  /** Initial font family. */
  fontFamily: FontFamily;
  /** Initial font size. */
  fontSize: number;
  /** Refs for theme values (for content hooks). */
  pageColorRef: RefObject<PageColor>;
  fontFamilyRef: RefObject<FontFamily>;
  fontSizeRef: RefObject<number>;
  /** Callback when locations are ready. */
  onLocationsReadyChange?: (ready: boolean) => void;
  /** Callback when location changes. */
  onLocationChange?: (
    cfi: string,
    progress: number,
    skipBackendUpdate?: boolean,
  ) => void;
  /** Ref indicating if this is the initial load. */
  isInitialLoadRef: RefObject<boolean>;
}

/**
 * Hook to create rendition callback handler.
 *
 * Creates a stable callback function for ReactReader's getRendition prop.
 * Handles rendition setup including theme application, initial CFI, and
 * location generation.
 *
 * Parameters
 * ----------
 * options : RenditionCallbackOptions
 *     Options for creating the callback.
 *
 * Returns
 * -------
 * (rendition: Rendition) => void
 *     Callback function to pass to ReactReader's getRendition prop.
 */
export function useRenditionCallback(options: RenditionCallbackOptions) {
  const {
    renditionRef,
    bookRef,
    initialCfi,
    applyInitialCfi,
    pageColorRef,
    fontFamilyRef,
    fontSizeRef,
    onLocationsReadyChange,
    onLocationChange,
    isInitialLoadRef,
  } = options;

  return useCallback(
    (rendition: Rendition) => {
      renditionRef.current = rendition;

      setupRendition({
        rendition,
        bookRef,
        initialCfi,
        applyInitialCfi,
        // Use refs for current values to ensure stable callback
        pageColor: pageColorRef.current,
        fontFamily: fontFamilyRef.current,
        fontSize: fontSizeRef.current,
        pageColorRef,
        fontFamilyRef,
        fontSizeRef,
        onLocationsReadyChange,
        onLocationChange,
        isInitialLoadRef,
      });

      // Fix: Check for non-linear start (e.g. cover wrapper) when no initialCfi is provided.
      // This ensures we skip wrappers and land on the first actual content page.
      if (!initialCfi) {
        const book = rendition.book;
        // biome-ignore lint/suspicious/noExplicitAny: Accessing internal spine structure
        const spine = (book as any).spine;

        if (spine) {
          // biome-ignore lint/suspicious/noExplicitAny: Dealing with untyped spine items
          let firstLinearItem: any = null;

          // Search for first linear item
          if (typeof spine.each === "function") {
            spine.each((item: any) => {
              if (item.linear !== "no" && !firstLinearItem) {
                firstLinearItem = item;
              }
            });
          }

          if (firstLinearItem) {
            rendition.display(firstLinearItem.href).catch(() => {
              // Ignore errors when trying to display the first linear item
            });
          }
        }
      }
    },
    [
      renditionRef,
      bookRef,
      initialCfi,
      applyInitialCfi,
      // Use refs instead of values to keep callback stable
      pageColorRef,
      fontFamilyRef,
      fontSizeRef,
      onLocationsReadyChange,
      onLocationChange,
      isInitialLoadRef,
    ],
  );
}
