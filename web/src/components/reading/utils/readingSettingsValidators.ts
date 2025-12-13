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

import { FONT_SIZE_MAX, FONT_SIZE_MIN } from "../constants/themeSettings";
import type {
  FontFamily,
  PageColor,
  PageLayout,
} from "../ReadingThemeSettings";

/**
 * Valid font families for reading settings.
 *
 * Centralized list of valid font families.
 * Follows SOC by separating validation data from components.
 */
const VALID_FONT_FAMILIES: readonly FontFamily[] = [
  "Literata",
  "Bookerly",
  "Amazon Ember",
  "OpenDyslexic",
  "Georgia",
  "Palatino",
  "Times New Roman",
  "Arial",
  "Helvetica",
  "Verdana",
  "Courier New",
  "Monaco",
] as const;

/**
 * Valid page colors for reading settings.
 *
 * Centralized list of valid page colors.
 * Follows SOC by separating validation data from components.
 */
const VALID_PAGE_COLORS: readonly PageColor[] = [
  "light",
  "dark",
  "sepia",
  "lightGreen",
] as const;

/**
 * Valid page layouts for reading settings.
 *
 * Centralized list of valid page layouts.
 * Follows SOC by separating validation data from components.
 */
const VALID_PAGE_LAYOUTS: readonly PageLayout[] = [
  "single",
  "two-column",
] as const;

/**
 * Validates if a string is a valid font family.
 *
 * Follows SRP by handling only font family validation.
 *
 * Parameters
 * ----------
 * value : string
 *     The value to validate.
 *
 * Returns
 * -------
 * boolean
 *     True if the value is a valid font family.
 */
export function isValidFontFamily(value: string): value is FontFamily {
  return VALID_FONT_FAMILIES.includes(value as FontFamily);
}

/**
 * Validates if a string is a valid page color.
 *
 * Follows SRP by handling only page color validation.
 *
 * Parameters
 * ----------
 * value : string
 *     The value to validate.
 *
 * Returns
 * -------
 * boolean
 *     True if the value is a valid page color.
 */
export function isValidPageColor(value: string): value is PageColor {
  return VALID_PAGE_COLORS.includes(value as PageColor);
}

/**
 * Validates if a string is a valid page layout.
 *
 * Follows SRP by handling only page layout validation.
 *
 * Parameters
 * ----------
 * value : string
 *     The value to validate.
 *
 * Returns
 * -------
 * boolean
 *     True if the value is a valid page layout.
 */
export function isValidPageLayout(value: string): value is PageLayout {
  return VALID_PAGE_LAYOUTS.includes(value as PageLayout);
}

/**
 * Validates and parses font size from string.
 *
 * Follows SRP by handling only font size validation and parsing.
 *
 * Parameters
 * ----------
 * value : string
 *     The string value to parse.
 * minSize : number
 *     Minimum valid font size (default: 12).
 * maxSize : number
 *     Maximum valid font size (default: 48).
 *
 * Returns
 * -------
 * number | null
 *     Parsed font size if valid, null otherwise.
 */
export function parseFontSize(
  value: string,
  minSize = FONT_SIZE_MIN,
  maxSize = FONT_SIZE_MAX,
): number | null {
  const parsed = parseInt(value, 10);
  if (Number.isNaN(parsed) || parsed < minSize || parsed > maxSize) {
    return null;
  }
  return parsed;
}

/**
 * Gets default font family.
 *
 * Returns
 * -------
 * FontFamily
 *     Default font family value.
 */
export function getDefaultFontFamily(): FontFamily {
  return "Bookerly";
}

/**
 * Gets default font size.
 *
 * Returns
 * -------
 * number
 *     Default font size value.
 */
export function getDefaultFontSize(): number {
  return 16;
}

/**
 * Gets default page color.
 *
 * Returns
 * -------
 * PageColor
 *     Default page color value.
 */
export function getDefaultPageColor(): PageColor {
  // Keep reading defaults aligned with the app theme when the user has not set
  // a dedicated reading page color yet. This avoids a "light" flash in the reader
  // footer/progress UI for first-time users when the app theme is dark.
  //
  // We intentionally avoid importing `useTheme` here to keep this module free of
  // React dependencies and to prevent circular imports.
  if (typeof document !== "undefined") {
    const themeAttr = document.documentElement.getAttribute("data-theme");
    if (themeAttr === "dark" || themeAttr === "light") {
      return themeAttr;
    }
  }

  if (typeof window !== "undefined") {
    try {
      // This key is also used by `web/src/hooks/useTheme.ts`.
      const storedTheme = localStorage.getItem("theme-preference");
      if (storedTheme === "dark" || storedTheme === "light") {
        return storedTheme;
      }
    } catch {
      // localStorage might not be available (privacy mode, SSR, etc.)
    }

    // Fallback to system preference if no explicit theme was stored.
    if (
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      return "dark";
    }
  }

  return "light";
}

/**
 * Gets default page layout.
 *
 * Returns
 * -------
 * PageLayout
 *     Default page layout value.
 */
export function getDefaultPageLayout(): PageLayout {
  return "two-column";
}
