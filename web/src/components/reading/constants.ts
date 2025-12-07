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

import type { FontFamily, PageLayout } from "./ReadingThemeSettings";

/**
 * Default values for reading settings.
 *
 * Single source of truth for default reading configuration.
 * Follows DRY by centralizing default values.
 * Follows SOC by separating constants from component logic.
 */
export const READING_DEFAULTS = {
  fontSize: 16,
  zoomLevel: 1.0,
  pageLayout: "two-column" as PageLayout,
  fontFamily: "Bookerly" as FontFamily,
  spreadMode: true,
} as const;
