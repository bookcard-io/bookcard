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

import styles from "./WithSelectedDropdown.module.scss";

export interface WithSelectedDropdownProps {
  /**
   * Callback fired when the dropdown is clicked.
   */
  onClick?: () => void;
}

/**
 * Dropdown button component for bulk actions on selected items.
 *
 * Provides a dropdown interface for performing actions on multiple selected items.
 */
export function WithSelectedDropdown({ onClick }: WithSelectedDropdownProps) {
  const handleClick = () => {
    onClick?.();
  };

  return (
    <button
      type="button"
      className={styles.dropdown}
      onClick={handleClick}
      aria-label="Actions with selected items"
      aria-haspopup="true"
    >
      <span className={styles.dropdownText}>With selected</span>
      <i
        className={`pi pi-chevron-down ${styles.chevronIcon}`}
        aria-hidden="true"
      />
    </button>
  );
}
