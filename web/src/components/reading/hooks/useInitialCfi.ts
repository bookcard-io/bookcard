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

import type { Rendition } from "epubjs";
import type { RefObject } from "react";
import { useEffect, useRef } from "react";

/**
 * Hook to manage initial CFI application logic.
 *
 * Handles applying the initial CFI location when both the CFI and rendition
 * are available, ensuring the saved reading position is restored.
 *
 * Parameters
 * ----------
 * initialCfi : string | null | undefined
 *     Initial CFI location to jump to.
 * renditionRef : RefObject<Rendition | undefined>
 *     Ref to the current rendition instance.
 * isNavigatingRef : RefObject<boolean>
 *     Ref indicating if navigation is in progress.
 * locationRef : RefObject<string | number>
 *     Ref to current location value.
 * setLocation : (loc: string | number) => void
 *     State setter for location.
 *
 * Returns
 * -------
 * object
 *     Object with applyInitialCfi function for use in rendition setup.
 */
export function useInitialCfi(
  initialCfi: string | null | undefined,
  renditionRef: RefObject<Rendition | undefined>,
  isNavigatingRef: RefObject<boolean>,
  locationRef: RefObject<string | number>,
  setLocation: (loc: string | number) => void,
) {
  const hasAppliedInitialCfiRef = useRef(false);

  // Apply initialCfi only once when both initialCfi and rendition are available
  // NOTE: We intentionally don't include 'location' in deps to avoid resetting on page turns
  // The effect should only run when initialCfi changes, not when location changes
  // Refs are stable objects and don't need to be in deps
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    // Only apply if:
    // 1. We have an initialCfi
    // 2. We haven't applied it yet
    // 3. Rendition is ready
    // 4. We're not currently navigating
    if (
      initialCfi &&
      !hasAppliedInitialCfiRef.current &&
      renditionRef.current &&
      !isNavigatingRef.current
    ) {
      const currentLocation = locationRef.current;
      // If location already matches initialCfi (from initialization), just mark as applied
      if (
        typeof currentLocation === "string" &&
        currentLocation === initialCfi
      ) {
        hasAppliedInitialCfiRef.current = true;
      } else if (
        currentLocation === 0 ||
        typeof currentLocation === "number" ||
        (typeof currentLocation === "string" && currentLocation !== initialCfi)
      ) {
        // Apply initialCfi if location is at initial value or doesn't match
        hasAppliedInitialCfiRef.current = true;
        isNavigatingRef.current = true;
        setLocation(initialCfi);
        // Reset flag after a short delay
        setTimeout(() => {
          isNavigatingRef.current = false;
        }, 100);
      }
    }
  }, [
    initialCfi,
    setLocation,
    // Refs are stable objects - included only to satisfy exhaustive-deps
    renditionRef,
    isNavigatingRef,
    locationRef,
  ]);

  // Expose function to apply initial CFI when rendition becomes ready
  return {
    applyInitialCfi: () => {
      if (
        initialCfi &&
        !hasAppliedInitialCfiRef.current &&
        !isNavigatingRef.current
      ) {
        hasAppliedInitialCfiRef.current = true;
        isNavigatingRef.current = true;
        setLocation(initialCfi);
        setTimeout(() => {
          isNavigatingRef.current = false;
        }, 100);
      }
    },
  };
}
