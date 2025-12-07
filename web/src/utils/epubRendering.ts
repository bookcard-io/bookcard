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

import type { Contents, Rendition } from "epubjs";
import type {
  FontFamily,
  PageColor,
} from "@/components/reading/ReadingThemeSettings";
import { fontSizeToPercent, generateFontFaces } from "@/utils/readingFonts";
import { getThemeColors, type ThemeColors } from "@/utils/readingTheme";

/**
 * EPUB rendering utilities.
 *
 * Centralized utilities for applying themes and styles to EPUB.js renditions
 * and documents. Follows SRP by separating rendering logic from UI components.
 * Follows DRY by eliminating theme application duplication.
 */

/**
 * Apply theme colors and typography to an EPUB.js rendition.
 *
 * Parameters
 * ----------
 * rendition : Rendition
 *     The EPUB.js rendition instance to theme.
 * pageColor : PageColor
 *     Logical page color theme used to derive base colors.
 * fontFamily : FontFamily
 *     Font family used for book content.
 * fontSize : number
 *     Font size in pixels, converted to percentage internally.
 */
export function applyThemeToRendition(
  rendition: Rendition,
  pageColor: PageColor,
  fontFamily: FontFamily,
  fontSize: number,
): void {
  const themes = rendition.themes;
  const colors = getThemeColors(pageColor);

  themes.override("color", colors.textColor);
  themes.override("background", colors.backgroundColor);
  themes.override("font-family", `"${fontFamily}"`);
  themes.fontSize(fontSizeToPercent(fontSize));
}

/**
 * Ensure that custom reading fonts are injected into the EPUB document.
 *
 * Parameters
 * ----------
 * document : Document
 *     The EPUB content document where font faces should be injected.
 */
export function ensureFontFacesInjected(document: Document): void {
  const existingFontStyle = document.getElementById("epub-reader-fonts");
  if (existingFontStyle) {
    return;
  }

  const fontFacesCSS = generateFontFaces();
  const style = document.createElement("style");
  style.id = "epub-reader-fonts";
  style.appendChild(document.createTextNode(fontFacesCSS));
  document.head.appendChild(style);
}

/**
 * Apply theme colors directly to the EPUB document body and iframe container.
 *
 * Parameters
 * ----------
 * document : Document
 *     The EPUB content document to style.
 * colors : ThemeColors
 *     Theme colors object returned by ``getThemeColors``.
 */
export function applyDocumentTheme(
  document: Document,
  colors: ThemeColors,
  fontFamily?: string,
): void {
  if (document.body) {
    document.body.style.color = colors.textColor;
    document.body.style.backgroundColor = colors.backgroundColor;
    if (fontFamily) {
      document.body.style.setProperty("font-family", `"${fontFamily}"`, "important");
    }
  }

  // Inject global font override to handle specific element styles (e.g. p tags with serif)
  // This ensures user font preference overrides book-specific styles
  if (fontFamily) {
    const styleId = "epub-font-override";
    let style = document.getElementById(styleId) as HTMLStyleElement;
    if (!style) {
      style = document.createElement("style");
      style.id = styleId;
      document.head.appendChild(style);
    }
    // Target common text elements to override specific class styles
    // Exclude pre and code to preserve monospace formatting
    style.textContent = `
      p, span, div, h1, h2, h3, h4, h5, h6, a, li, blockquote, td, th, dt, dd {
        font-family: "${fontFamily}" !important;
      }
    `;
  }

  const iframe = document.querySelector("iframe");
  if (iframe?.contentDocument?.body) {
    iframe.contentDocument.body.style.color = colors.textColor;
    iframe.contentDocument.body.style.backgroundColor = colors.backgroundColor;
    if (fontFamily) {
      iframe.contentDocument.body.style.setProperty("font-family", `"${fontFamily}"`, "important");
    }
  }
}

/**
 * Create a content hook handler for EPUB pages.
 *
 * Ensures fonts and themes are applied to all pages as they load.
 * Uses refs to access latest theme values since hook closure captures initial values.
 *
 * Parameters
 * ----------
 * rendition : Rendition
 *     The EPUB.js rendition instance.
 * pageColorRef : React.RefObject<PageColor>
 *     Ref to current page color theme.
 * fontFamilyRef : React.RefObject<FontFamily>
 *     Ref to current font family.
 * fontSizeRef : React.RefObject<number>
 *     Ref to current font size in pixels.
 *
 * Returns
 * -------
 * (contents: Contents) => void
 *     Content hook handler function.
 */
export function createContentHook(
  rendition: Rendition,
  pageColorRef: React.RefObject<PageColor>,
  fontFamilyRef: React.RefObject<FontFamily>,
  fontSizeRef: React.RefObject<number>,
): (contents: Contents) => void {
  return (contents: Contents) => {
    // Get latest values from refs
    const currentPageColor = pageColorRef.current;
    const currentFontFamily = fontFamilyRef.current;
    const currentFontSize = fontSizeRef.current;

    const document = contents.window.document;
    if (!document) {
      return;
    }

    ensureFontFacesInjected(document);

    // Apply current theme settings using latest values from refs
    const currentColors = getThemeColors(currentPageColor);

    // Apply theme overrides using latest values
    applyThemeToRendition(
      rendition,
      currentPageColor,
      currentFontFamily,
      currentFontSize,
    );

    applyDocumentTheme(document, currentColors, currentFontFamily);
  };
}

/**
 * Refresh the current page to apply theme changes.
 *
 * Parameters
 * ----------
 * rendition : Rendition | undefined
 *     The EPUB.js rendition instance.
 * currentLocation : string | number
 *     Current location value.
 * isNavigatingRef : React.RefObject<boolean>
 *     Ref indicating if navigation is in progress.
 */
export function refreshPageForTheme(
  rendition: Rendition | undefined,
  currentLocation: string | number,
  isNavigatingRef: React.RefObject<boolean>,
): void {
  if (!rendition || !currentLocation || typeof currentLocation !== "string") {
    return;
  }

  try {
    // Use a small delay to ensure overrides are applied before refresh
    // Only refresh if we're not currently navigating (to avoid interfering with page turns)
    if (!isNavigatingRef.current) {
      setTimeout(() => {
        if (!isNavigatingRef.current && rendition) {
          rendition.display(currentLocation);
        }
      }, 50);
    }
  } catch (error) {
    console.warn("Could not refresh page for theme update:", error);
  }
}
