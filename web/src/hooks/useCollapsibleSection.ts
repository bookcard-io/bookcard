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

import { useEffect, useState } from "react";

export interface UseCollapsibleSectionOptions {
  /** Initial expanded state. */
  initialExpanded?: boolean;
  /** Whether to auto-expand when condition becomes true. */
  autoExpandOnCondition?: boolean;
  /** Condition to check for auto-expansion. */
  condition?: boolean;
}

export interface UseCollapsibleSectionResult {
  /** Whether the section is currently expanded. */
  isExpanded: boolean;
  /** Toggle expanded state. */
  toggle: () => void;
  /** Set expanded state explicitly. */
  setExpanded: (expanded: boolean) => void;
}

/**
 * Custom hook for managing collapsible section state.
 *
 * Handles expanded/collapsed state with optional auto-expansion based on conditions.
 * Follows SRP by focusing solely on collapsible state management.
 * Follows IOC by accepting configurable options.
 *
 * Parameters
 * ----------
 * options : UseCollapsibleSectionOptions
 *     Configuration for collapsible behavior.
 *
 * Returns
 * -------
 * UseCollapsibleSectionResult
 *     Expanded state and control functions.
 */
export function useCollapsibleSection(
  options: UseCollapsibleSectionOptions = {},
): UseCollapsibleSectionResult {
  const {
    initialExpanded = true,
    autoExpandOnCondition = false,
    condition = false,
  } = options;

  const [isExpanded, setIsExpanded] = useState(initialExpanded);

  // Auto-expand when condition becomes true
  useEffect(() => {
    if (autoExpandOnCondition && condition && !isExpanded) {
      setIsExpanded(true);
    }
  }, [autoExpandOnCondition, condition, isExpanded]);

  const toggle = () => {
    setIsExpanded((prev) => !prev);
  };

  const setExpanded = (expanded: boolean) => {
    setIsExpanded(expanded);
  };

  return {
    isExpanded,
    toggle,
    setExpanded,
  };
}
