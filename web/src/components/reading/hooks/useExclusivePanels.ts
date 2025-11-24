// Copyright (C) 2025 khoa and others
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

import { useMemo } from "react";

export interface Panel {
  /** Whether the panel is currently open. */
  isOpen: boolean;
  /** Function to close the panel. */
  close: () => void;
  /** Function to open the panel. */
  open: () => void;
}

export interface UseExclusivePanelsOptions {
  /** Array of panels to manage. */
  panels: Panel[];
  /** Whether mutual exclusivity is enabled. Defaults to true. */
  enabled?: boolean;
}

export interface UseExclusivePanelsReturn {
  /**
   * Array of wrapped open functions, one for each panel.
   * When a panel is opened, all other panels are closed first.
   * Functions are stable across renders.
   */
  openFunctions: (() => void)[];
}

/**
 * Hook for managing mutually exclusive panels.
 *
 * Ensures only one panel can be open at a time by closing
 * all other panels when one opens. This prevents multiple
 * panels from being open simultaneously.
 *
 * Follows SRP by managing only panel exclusivity logic.
 * Follows IOC by accepting panel instances as dependencies.
 * Follows KISS by using a simple array-based approach.
 *
 * Parameters
 * ----------
 * options : UseExclusivePanelsOptions
 *     Hook options including panels array and enabled flag.
 *
 * Returns
 * -------
 * UseExclusivePanelsReturn
 *     Array of wrapped open functions that ensure mutual exclusivity.
 *
 * Example
 * -------
 * ```tsx
 * const fontPanel = useFontPanel();
 * const searchPanel = useSearchPanel();
 *
 * const { openFunctions } = useExclusivePanels({
 *   panels: [fontPanel, searchPanel],
 *   enabled: true, // Set to false to disable mutual exclusivity
 * });
 *
 * const [openFontPanel, openSearchPanel] = openFunctions;
 * ```
 */
export function useExclusivePanels({
  panels,
  enabled = true,
}: UseExclusivePanelsOptions): UseExclusivePanelsReturn {
  const openFunctions = useMemo(
    () =>
      panels.map((panel, index) => {
        return () => {
          if (enabled) {
            // Close all other panels
            panels.forEach((otherPanel, otherIndex) => {
              if (otherIndex !== index && otherPanel.isOpen) {
                otherPanel.close();
              }
            });
          }
          // Open this panel
          panel.open();
        };
      }),
    [enabled, panels],
  );

  return {
    openFunctions,
  };
}
