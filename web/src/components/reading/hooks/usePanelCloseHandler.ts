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

import { useCallback } from "react";

import type { Panel } from "./useExclusivePanels";

/**
 * Hook for creating panel close handlers that also hide the header.
 *
 * Follows DRY by eliminating repetitive close handler patterns.
 * Follows SRP by separating panel close logic from component.
 * Follows IOC by accepting panel and hideHeader as dependencies.
 *
 * Parameters
 * ----------
 * panel : Panel
 *     Panel instance with close method.
 * hideHeader : () => void
 *     Function to hide the header.
 *
 * Returns
 * -------
 * () => void
 *     Close handler that closes the panel and hides the header.
 *
 * Example
 * -------
 * ```tsx
 * const fontPanel = useFontPanel();
 * const { hideHeader } = useHeaderVisibility();
 * const handleClose = usePanelCloseHandler(fontPanel, hideHeader);
 * ```
 */
export function usePanelCloseHandler(
  panel: Panel,
  hideHeader: () => void,
): () => void {
  return useCallback(() => {
    panel.close();
    hideHeader();
  }, [panel, hideHeader]);
}
