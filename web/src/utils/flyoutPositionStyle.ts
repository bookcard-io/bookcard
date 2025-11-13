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

import type { FlyoutPosition } from "@/hooks/useFlyoutPosition";

/**
 * Calculate CSS style object for flyout menu position.
 *
 * Converts position and direction into React style object.
 * Follows SRP by handling only style calculation.
 * Follows DRY by centralizing position-to-style conversion.
 *
 * Parameters
 * ----------
 * position : FlyoutPosition
 *     Position coordinates.
 * direction : "left" | "right"
 *     Direction the flyout should fly.
 *
 * Returns
 * -------
 * React.CSSProperties
 *     CSS style object for positioning the flyout menu.
 */
export function getFlyoutPositionStyle(
  position: FlyoutPosition,
  direction: "left" | "right",
): React.CSSProperties {
  return {
    top: `${position.top}px`,
    ...(direction === "right" && position.left !== undefined
      ? { left: `${position.left}px` }
      : {}),
    ...(direction === "left" && position.right !== undefined
      ? { right: `${position.right}px` }
      : {}),
  };
}
