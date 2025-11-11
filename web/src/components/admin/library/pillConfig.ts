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
