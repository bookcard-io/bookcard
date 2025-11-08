"use client";

import { ViewModeButton } from "./ViewModeButton";
import styles from "./ViewModeButtons.module.scss";

export type ViewMode = "sort" | "grid" | "list";

export interface ViewModeButtonsProps {
  /**
   * Currently active view mode.
   */
  activeMode?: ViewMode;
  /**
   * Current sort order (used to determine sort icon).
   */
  sortOrder?: "asc" | "desc";
  /**
   * Callback fired when a view mode is selected.
   */
  onModeChange?: (mode: ViewMode) => void;
}

/**
 * Container component for view mode toggle buttons.
 *
 * Manages multiple view mode options (sort, grid, list) and their active state.
 * Follows SRP by handling only view mode selection UI.
 */
export function ViewModeButtons({
  activeMode = "grid",
  sortOrder = "desc",
  onModeChange,
}: ViewModeButtonsProps) {
  const handleModeChange = (mode: ViewMode) => {
    onModeChange?.(mode);
  };

  // Determine sort icon based on current sort order
  const sortIconClass =
    sortOrder === "asc" ? "pi-sort-amount-down-alt" : "pi-sort-amount-up";

  return (
    <fieldset className={styles.viewModeButtons} aria-label="View mode options">
      <legend className={styles.legend}>View mode options</legend>
      <ViewModeButton
        iconClass={sortIconClass}
        isActive={activeMode === "sort"}
        onClick={() => handleModeChange("sort")}
        ariaLabel="Sort view"
      />
      <ViewModeButton
        iconClass="pi-th-large"
        isActive={activeMode === "grid"}
        onClick={() => handleModeChange("grid")}
        ariaLabel="Grid view"
      />
      <ViewModeButton
        iconClass="pi-list"
        isActive={activeMode === "list"}
        onClick={() => handleModeChange("list")}
        ariaLabel="List view"
      />
    </fieldset>
  );
}
