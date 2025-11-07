"use client";

import { GridView } from "@/icons/GridView";
import { ListSort } from "@/icons/ListSort";
import { ListView } from "@/icons/ListView";
import { ViewModeButton } from "./ViewModeButton";
import styles from "./ViewModeButtons.module.scss";

export type ViewMode = "sort" | "grid" | "list";

export interface ViewModeButtonsProps {
  /**
   * Currently active view mode.
   */
  activeMode?: ViewMode;
  /**
   * Callback fired when a view mode is selected.
   */
  onModeChange?: (mode: ViewMode) => void;
}

/**
 * Container component for view mode toggle buttons.
 *
 * Manages multiple view mode options (sort, grid, list) and their active state.
 */
export function ViewModeButtons({
  activeMode = "grid",
  onModeChange,
}: ViewModeButtonsProps) {
  const handleModeChange = (mode: ViewMode) => {
    onModeChange?.(mode);
  };

  return (
    <fieldset className={styles.viewModeButtons} aria-label="View mode options">
      <legend className={styles.legend}>View mode options</legend>
      <ViewModeButton
        icon={ListSort}
        isActive={activeMode === "sort"}
        onClick={() => handleModeChange("sort")}
        ariaLabel="Sort view"
      />
      <ViewModeButton
        icon={GridView}
        isActive={activeMode === "grid"}
        onClick={() => handleModeChange("grid")}
        ariaLabel="Grid view"
      />
      <ViewModeButton
        icon={ListView}
        isActive={activeMode === "list"}
        onClick={() => handleModeChange("list")}
        ariaLabel="List view"
      />
    </fieldset>
  );
}
