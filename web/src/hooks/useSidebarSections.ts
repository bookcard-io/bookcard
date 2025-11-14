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

import { useCallback, useState } from "react";

export interface UseSidebarSectionsResult {
  /** Set of expanded section titles. */
  expandedSections: Set<string>;
  /** Toggle a section's expanded state. */
  toggleSection: (title: string) => void;
}

/**
 * Hook for managing sidebar section expansion state.
 *
 * Handles collapsible section state management.
 * Follows SRP by handling only section state logic.
 *
 * Parameters
 * ----------
 * initialSections : string[]
 *     Initial list of expanded section titles.
 *
 * Returns
 * -------
 * UseSidebarSectionsResult
 *     Object containing expanded sections state and toggle function.
 */
export function useSidebarSections(
  initialSections: string[] = ["MY LIBRARY", "MY SHELVES", "DEVICES"],
): UseSidebarSectionsResult {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(initialSections),
  );

  const toggleSection = useCallback((title: string) => {
    setExpandedSections((prev) => {
      const newExpanded = new Set(prev);
      if (newExpanded.has(title)) {
        newExpanded.delete(title);
      } else {
        newExpanded.add(title);
      }
      return newExpanded;
    });
  }, []);

  return { expandedSections, toggleSection };
}
