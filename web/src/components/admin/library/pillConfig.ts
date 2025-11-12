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
 * Pill configuration for library statistics.
 *
 * Defines how each statistic pill should be displayed.
 * Follows SRP by separating configuration from presentation.
 * Follows IOC by allowing dependency injection of formatters.
 * Follows DRY by centralizing pill definitions.
 */

import type { LibraryStats } from "@/services/libraryStatsService";
import { formatFileSize } from "@/utils/format";

/**
 * Formatter function for a statistic value.
 *
 * Parameters
 * ----------
 * value : number
 *     The statistic value to format.
 *
 * Returns
 * -------
 * string
 *     Formatted value string.
 */
export type StatFormatter = (value: number) => string;

/**
 * Configuration for a single statistic pill.
 *
 * Follows SRP by encapsulating pill display configuration.
 */
export interface PillConfig {
  /** Key in LibraryStats to read the value from. */
  statKey: keyof LibraryStats;
  /** Label to display (e.g., "BOOKS", "SERIES"). */
  label: string;
  /** Formatter function to convert number to display string. */
  formatter: StatFormatter;
}

/**
 * Default number formatter (locale string with commas).
 *
 * Parameters
 * ----------
 * value : number
 *     Number to format.
 *
 * Returns
 * -------
 * string
 *     Formatted number string.
 */
const formatNumber: StatFormatter = (value: number): string => {
  return value.toLocaleString();
};

/**
 * Configuration for all library statistic pills.
 *
 * To add a new pill, simply add a new entry to this array.
 * Follows Open/Closed Principle - open for extension, closed for modification.
 */
export const LIBRARY_STATS_PILL_CONFIG: readonly PillConfig[] = [
  {
    statKey: "total_books",
    label: "BOOKS",
    formatter: formatNumber,
  },
  {
    statKey: "total_series",
    label: "SERIES",
    formatter: formatNumber,
  },
  {
    statKey: "total_authors",
    label: "AUTHORS",
    formatter: formatNumber,
  },
  {
    statKey: "total_tags",
    label: "TAGS",
    formatter: formatNumber,
  },
  {
    statKey: "total_ratings",
    label: "RATINGS",
    formatter: formatNumber,
  },
  {
    statKey: "total_content_size",
    label: "CONTENT",
    formatter: formatFileSize,
  },
] as const;
