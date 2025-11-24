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

import type { IReactReaderStyle } from "react-reader";
import { ReactReaderStyle } from "react-reader";
import type { PageColor } from "@/components/reading/ReadingThemeSettings";
import { getThemeColors, getTocColors } from "@/utils/readingTheme";

/**
 * EPUB reader style utilities.
 *
 * Centralized utilities for creating ReactReader styles and TOC hover styles.
 * Follows SRP by separating style generation from UI components.
 * Follows DRY by eliminating style creation duplication.
 */

/**
 * Create ReactReader styles for a given page color theme.
 *
 * Parameters
 * ----------
 * pageColor : PageColor
 *     Logical page color theme.
 *
 * Returns
 * -------
 * IReactReaderStyle
 *     Style configuration for ``ReactReader``.
 */
export function createReaderStyles(pageColor: PageColor): IReactReaderStyle {
  const colors = getThemeColors(pageColor);
  const tocColors = getTocColors(pageColor);
  const isDark = pageColor === "dark";

  if (isDark) {
    // Dark theme - white text on dark background
    return {
      ...ReactReaderStyle,
      arrow: {
        ...ReactReaderStyle.arrow,
        color: "#fff",
      },
      arrowHover: {
        ...ReactReaderStyle.arrowHover,
        color: "#ccc",
      },
      readerArea: {
        ...ReactReaderStyle.readerArea,
        backgroundColor: colors.backgroundColor,
        transition: undefined,
      },
      titleArea: {
        ...ReactReaderStyle.titleArea,
        color: "#ccc",
      },
      tocArea: {
        ...ReactReaderStyle.tocArea,
        background: tocColors.background,
      },
      tocAreaButton: {
        ...ReactReaderStyle.tocAreaButton,
        color: tocColors.buttonTextColor,
        borderBottom: `1px solid ${tocColors.borderColor}`,
      },
      tocBackground: {
        ...ReactReaderStyle.tocBackground,
        background: tocColors.overlayBackground,
      },
      tocButtonExpanded: {
        ...ReactReaderStyle.tocButtonExpanded,
        background: tocColors.background,
      },
      tocButtonBar: {
        ...ReactReaderStyle.tocButtonBar,
        background: tocColors.textColor,
      },
      tocButton: {
        ...ReactReaderStyle.tocButton,
        color: "white",
        display: "none",
      },
    };
  }

  // Light, sepia, or lightGreen theme
  return {
    ...ReactReaderStyle,
    readerArea: {
      ...ReactReaderStyle.readerArea,
      backgroundColor: colors.backgroundColor,
      transition: undefined,
    },
    titleArea: {
      ...ReactReaderStyle.titleArea,
      color: colors.textColor,
    },
    tocArea: {
      ...ReactReaderStyle.tocArea,
      background: tocColors.background,
    },
    tocAreaButton: {
      ...ReactReaderStyle.tocAreaButton,
      color: tocColors.buttonTextColor,
      borderBottom: `1px solid ${tocColors.borderColor}`,
    },
    tocBackground: {
      ...ReactReaderStyle.tocBackground,
      background: tocColors.overlayBackground,
    },
    tocButtonExpanded: {
      ...ReactReaderStyle.tocButtonExpanded,
      background: tocColors.background,
    },
    tocButton: {
      ...ReactReaderStyle.tocButton,
      display: "none",
    },
  };
}

/**
 * Create CSS for TOC hover styles based on the current page color theme.
 *
 * Parameters
 * ----------
 * pageColor : PageColor
 *     Logical page color theme.
 *
 * Returns
 * -------
 * string
 *     CSS string applied in a ``<style>`` tag for TOC hover behavior.
 */
export function createTocHoverStyles(pageColor: PageColor): string {
  const tocColors = getTocColors(pageColor);
  const isDark = pageColor === "dark";

  return `
      /* TOC button hover styles */
      div[style*="overflowY"] button:hover {
        background-color: ${
          isDark ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.05)"
        } !important;
        color: ${tocColors.buttonHoverColor} !important;
        transition: background-color 0.2s ease, color 0.2s ease;
      }
    `;
}
