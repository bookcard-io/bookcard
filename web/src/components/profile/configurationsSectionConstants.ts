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
    label: "Content & Metadata",
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
