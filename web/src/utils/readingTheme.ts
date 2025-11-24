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

import type { PageColor } from "@/components/reading/ReadingThemeSettings";

/**
 * Reading theme utilities.
 *
 * Centralized theme color calculations for reading components.
 * Follows SRP by separating theme logic from UI components.
 * Follows DRY by eliminating color calculation duplication.
 */

/**
 * Theme colors for reading area.
 */
export interface ThemeColors {
  /** Text color. */
  textColor: string;
  /** Background color. */
  backgroundColor: string;
}

/**
 * TOC (Table of Contents) colors.
 */
export interface TocColors {
  /** TOC background color. */
  background: string;
  /** TOC text color. */
  textColor: string;
  /** TOC button text color. */
  buttonTextColor: string;
  /** TOC button hover color. */
  buttonHoverColor: string;
  /** TOC border color. */
  borderColor: string;
  /** TOC overlay background color. */
  overlayBackground: string;
}

/**
 * Get theme colors for reading area based on page color.
 *
 * Parameters
 * ----------
 * pageColor : PageColor
 *     The page color theme.
 *
 * Returns
 * -------
 * ThemeColors
 *     Theme colors for text and background.
 */
export function getThemeColors(pageColor: PageColor): ThemeColors {
  switch (pageColor) {
    case "dark":
      return { textColor: "#fff", backgroundColor: "#0b0e14" };
    case "sepia":
      return { textColor: "#000", backgroundColor: "#f4e4c1" };
    case "lightGreen":
      return { textColor: "#000", backgroundColor: "#e8f5e9" };
    default: // light
      return { textColor: "#000", backgroundColor: "#f1f1f1" };
  }
}

/**
 * Get TOC colors based on page color theme.
 *
 * Parameters
 * ----------
 * pageColor : PageColor
 *     The page color theme.
 *
 * Returns
 * -------
 * TocColors
 *     TOC colors for various UI elements.
 */
export function getTocColors(pageColor: PageColor): TocColors {
  switch (pageColor) {
    case "dark":
      return {
        background: "#1a1d24",
        textColor: "#e0e0e0",
        buttonTextColor: "#ccc",
        buttonHoverColor: "#fff",
        borderColor: "#333",
        overlayBackground: "rgba(0, 0, 0, 0.5)",
      };
    case "sepia":
      return {
        background: "#e8d9b8",
        textColor: "#2a2a2a",
        buttonTextColor: "#555",
        buttonHoverColor: "#000",
        borderColor: "#d4c5a4",
        overlayBackground: "rgba(0, 0, 0, 0.3)",
      };
    case "lightGreen":
      return {
        background: "#d4e8d5",
        textColor: "#1a3a1a",
        buttonTextColor: "#2d5a2d",
        buttonHoverColor: "#000",
        borderColor: "#c0d8c1",
        overlayBackground: "rgba(0, 0, 0, 0.2)",
      };
    default: // light
      return {
        background: "#e8e8e8",
        textColor: "#333",
        buttonTextColor: "#666",
        buttonHoverColor: "#000",
        borderColor: "#d0d0d0",
        overlayBackground: "rgba(0, 0, 0, 0.3)",
      };
  }
}

/**
 * Get background color for controls based on page color.
 *
 * Parameters
 * ----------
 * pageColor : PageColor
 *     The page color theme.
 *
 * Returns
 * -------
 * string
 *     Background color hex string.
 */
export function getControlBackgroundColor(pageColor: PageColor): string {
  return getThemeColors(pageColor).backgroundColor;
}
