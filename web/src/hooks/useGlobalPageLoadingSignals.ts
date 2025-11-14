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

import { useMemo } from "react";
import { useLibraryLoading } from "@/contexts/LibraryLoadingContext";
import { useShelvesContext } from "@/contexts/ShelvesContext";
import { useUser } from "@/contexts/UserContext";

/**
 * Aggregate global loading signals for the page-level overlay.
 *
 * Encapsulates which domains are considered "page critical" so that
 * `PageLoadingOverlay` does not need to know about individual data sources.
 * New global loading domains (e.g., store, video) can be added here without
 * changing the overlay component itself.
 *
 * Parameters
 * ----------
 * isNavTransition : boolean
 *     Whether a navigation or query-string transition is currently active.
 *
 * Returns
 * -------
 * boolean
 *     True if any page-critical loading operation is in progress.
 */
export function useGlobalPageLoadingSignals(isNavTransition: boolean): boolean {
  const { isLoading: isUserLoading } = useUser();
  const { isLoading: isShelvesLoading } = useShelvesContext();

  // NOTE: Including books loading in the global overlay is a product decision
  // and may be revisited if the spinner becomes too noisy for normal usage.
  const { isBooksLoading } = useLibraryLoading();

  return useMemo(
    () =>
      isUserLoading || isShelvesLoading || isBooksLoading || isNavTransition,
    [isUserLoading, isShelvesLoading, isBooksLoading, isNavTransition],
  );
}
