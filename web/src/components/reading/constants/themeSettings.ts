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

import type { FontFamily, PageColor } from "../ReadingThemeSettings";

/**
 * Available font families for the reader.
 *
 * Follows IOC by centralizing configuration.
 */
export const AVAILABLE_FONT_FAMILIES: FontFamily[] = [
  "Bookerly",
  "Amazon Ember",
  "OpenDyslexic",
];

/**
 * Configuration for page color themes.
 *
 * Follows IOC by centralizing color configuration.
 */
export interface PageColorConfig {
  /** Color value for the theme. */
  backgroundColor: string;
  /** App theme to use with this page color. */
  appTheme: "light" | "dark";
  /** Accessibility label. */
  ariaLabel: string;
}

/**
 * Page color theme configurations.
 */
export const PAGE_COLOR_CONFIGS: Record<PageColor, PageColorConfig> = {
  light: {
    backgroundColor: "var(--clr-surface-a0)",
    appTheme: "light",
    ariaLabel: "Light theme",
  },
  dark: {
    backgroundColor: "#000",
    appTheme: "dark",
    ariaLabel: "Dark theme",
  },
  sepia: {
    backgroundColor: "#f4e4c1",
    appTheme: "light",
    ariaLabel: "Sepia theme",
  },
  lightGreen: {
    backgroundColor: "#e8f5e9",
    appTheme: "light",
    ariaLabel: "Light green theme",
  },
};

/**
 * Font size constraints.
 */
export const FONT_SIZE_MIN = 12;
export const FONT_SIZE_MAX = 36;
export const FONT_SIZE_STEP = 1;
