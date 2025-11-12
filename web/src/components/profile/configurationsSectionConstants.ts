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

/**
 * Configuration constants for ConfigurationsSection component.
 *
 * Follows SOC by separating data definitions from component logic.
 */

/**
 * Tab ID type for configuration sections.
 */
export type TabId =
  | "display"
  | "sorting"
  | "navigation"
  | "deletion"
  | "content";

/**
 * Tab configuration interface.
 *
 * Follows SOC by separating tab metadata from component rendering.
 */
export interface TabConfig {
  /** Unique identifier for the tab. */
  id: TabId;
  /** Display label for the tab. */
  label: string;
}

/**
 * Configuration tabs for user preferences.
 *
 * Centralized tab definitions following SOC by separating data from components.
 * Follows DRY by avoiding duplication of tab structure.
 */
export const CONFIGURATION_TABS: readonly TabConfig[] = [
  {
    id: "display",
    label: "Display & Layout",
  },
  {
    id: "sorting",
    label: "Sorting & Organization",
  },
  {
    id: "content",
    label: "Uploads & Metadata",
  },
  {
    id: "navigation",
    label: "Navigation & Interaction",
  },
  {
    id: "deletion",
    label: "Deletion Preferences",
  },
] as const;

/**
 * Default active tab ID.
 */
export const DEFAULT_TAB_ID: TabId = "display";
