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
import { useEffect } from "react";
import {
  applyDocumentTheme,
  applyThemeToRendition,
  refreshPageForTheme,
} from "@/utils/epubRendering";
import { getThemeColors } from "@/utils/readingTheme";
import type { FontFamily, PageColor } from "../ReadingThemeSettings";

/**
 * Options for useEpubTheme hook.
 */
export interface UseEpubThemeOptions {
  /** Ref to rendition instance. */
  renditionRef: RefObject<Rendition | undefined>;
  /** Ref to current location. */
  locationRef: RefObject<string | number>;
  /** Ref indicating if navigation is in progress. */
  isNavigatingRef: RefObject<boolean>;
  /** Page color theme. */
  pageColor: PageColor;
  /** Font family. */
  fontFamily: FontFamily;
  /** Font size in pixels. */
  fontSize: number;
}

/**
 * Hook to manage EPUB theme updates.
 *
 * Applies theme changes to the rendition and refreshes the page when needed.
 * Follows SRP by focusing solely on theme management.
 * Follows IOC by accepting dependencies as parameters.
 *
 * Parameters
 * ----------
 * options : UseEpubThemeOptions
 *     Hook options including refs and theme values.
 */
export function useEpubTheme({
  renditionRef,
  locationRef,
  isNavigatingRef,
  pageColor,
  fontFamily,
  fontSize,
}: UseEpubThemeOptions): void {
  useEffect(() => {
    if (!renditionRef.current) {
      return;
    }

    const rendition = renditionRef.current;
    applyThemeToRendition(rendition, pageColor, fontFamily, fontSize);

    // Apply document theme (font/colors) to currently visible content immediately
    // This handles the manual DOM manipulations like global style injection that applyThemeToRendition misses
    const contents = rendition.getContents();
    if (contents && Array.isArray(contents)) {
      const colors = getThemeColors(pageColor);
      contents.forEach((content) => {
        if (content.document) {
          applyDocumentTheme(content.document, colors, fontFamily);
        }
      });
    } else if (contents) {
      // Single content object case
      const contentList = [contents];
      contentList.forEach((content) => {
        if (content.document) {
          const colors = getThemeColors(pageColor);
          applyDocumentTheme(content.document, colors, fontFamily);
        }
      });
    }

    // Force refresh of the current page to apply theme changes immediately
    // Only refresh if we're not currently navigating (checked inside refreshPageForTheme)
    refreshPageForTheme(rendition, locationRef.current, isNavigatingRef);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    fontFamily,
    fontSize,
    pageColor,
    renditionRef,
    isNavigatingRef,
    locationRef,
  ]);
}
