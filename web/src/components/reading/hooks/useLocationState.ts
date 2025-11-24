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

import { useEffect, useRef, useState } from "react";

/**
 * Hook to manage location state and ref synchronization.
 *
 * Maintains both state and ref for location to allow access in effects
 * without including location in dependency arrays (preventing unnecessary
 * re-renders and effect re-runs).
 *
 * Parameters
 * ----------
 * initialLocation : string | number
 *     Initial location value.
 *
 * Returns
 * -------
 * object
 *     Object containing location state, setter, and ref.
 */
export function useLocationState(initialLocation: string | number) {
  const [location, setLocation] = useState<string | number>(initialLocation);
  const locationRef = useRef<string | number>(location);

  // Keep ref in sync with state
  useEffect(() => {
    locationRef.current = location;
  }, [location]);

  return {
    location,
    setLocation,
    locationRef,
  };
}
