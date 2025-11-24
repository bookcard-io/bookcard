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

import { useEffect, useRef, useState } from "react";

/**
 * Hook for managing header visibility with auto-hide behavior.
 *
 * Handles visibility state transitions when locations become ready.
 * Follows SRP by separating visibility logic from UI component.
 * Follows IOC by providing a reusable hook interface.
 *
 * Parameters
 * ----------
 * areLocationsReady : boolean
 *     Whether EPUB locations are ready.
 * keepVisible : boolean
 *     Whether to force header to remain visible (e.g., when panel is open).
 *
 * Returns
 * -------
 * object
 *     Visibility state and handlers.
 */
export function useHeaderVisibility(
  areLocationsReady: boolean,
  keepVisible: boolean = false,
) {
  const [hasLocationsBeenReady, setHasLocationsBeenReady] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const hideTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Track when locations become ready to transition to normal hover behavior
  useEffect(() => {
    if (hideTimeoutRef.current) {
      clearTimeout(hideTimeoutRef.current);
      hideTimeoutRef.current = null;
    }

    if (areLocationsReady && !hasLocationsBeenReady) {
      // Hide header when locations become ready (with a small delay for smooth transition)
      hideTimeoutRef.current = setTimeout(() => {
        setHasLocationsBeenReady(true);
        setIsVisible(false);
        hideTimeoutRef.current = null;
      }, 500);
    }

    return () => {
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current);
        hideTimeoutRef.current = null;
      }
    };
  }, [areLocationsReady, hasLocationsBeenReady]);

  // Keep header visible when keepVisible is true
  useEffect(() => {
    if (keepVisible) {
      setIsVisible(true);
    }
  }, [keepVisible]);

  // Show on mouse enter (only works after locations have been ready)
  const handleMouseEnter = () => {
    if (hasLocationsBeenReady) {
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current);
        hideTimeoutRef.current = null;
      }
      setIsVisible(true);
    }
  };

  // Hide immediately on mouse leave (only works after locations have been ready)
  const handleMouseLeave = () => {
    if (hasLocationsBeenReady && !keepVisible) {
      setIsVisible(false);
    }
  };

  return {
    isVisible,
    handleMouseEnter,
    handleMouseLeave,
  };
}
