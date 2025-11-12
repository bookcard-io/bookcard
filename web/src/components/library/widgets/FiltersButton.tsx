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

"use client";

import { countActiveFilterTypes } from "@/utils/filters";
import styles from "./FiltersButton.module.scss";
import type { FilterValues } from "./FiltersPanel";

export interface FiltersButtonProps {
  /**
   * Callback fired when the filters button is clicked.
   */
  onClick?: () => void;
  /**
   * Current filter values for displaying active filter count.
   */
  filters?: FilterValues;
}

/**
 * Button component for opening the filters panel.
 *
 * Displays a filter icon and label for accessing filter options.
 * Shows a badge with the count of active filter types when filters are active.
 */
export function FiltersButton({ onClick, filters }: FiltersButtonProps) {
  const handleClick = () => {
    onClick?.();
  };

  const activeFilterCount = countActiveFilterTypes(filters);
  const ariaLabel =
    activeFilterCount > 0
      ? `Open filters (${activeFilterCount} active)`
      : "Open filters";

  return (
    <button
      type="button"
      className={styles.filtersButton}
      onClick={handleClick}
      aria-label={ariaLabel}
      data-filters-button
    >
      <div className={styles.buttonContent}>
        <i className="pi pi-filter" aria-hidden="true" />
        <span className={styles.buttonText}>Filters</span>
      </div>
      {activeFilterCount > 0 && (
        <span className={styles.badge} aria-hidden="true">
          {activeFilterCount}
        </span>
      )}
    </button>
  );
}
