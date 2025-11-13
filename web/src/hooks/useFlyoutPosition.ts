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

/** Overlap amount between parent menu and flyout menu in pixels. */
const FLYOUT_OVERLAP = 2;

/** Approximate width of the flyout menu in pixels. */
const FLYOUT_MENU_WIDTH = 200;

export interface FlyoutPosition {
  /** Top position in pixels. */
  top: number;
  /** Left position in pixels (when flying right). */
  left?: number;
  /** Right position in pixels (when flying left). */
  right?: number;
}

export interface UseFlyoutPositionOptions {
  /** Whether the flyout is open. */
  isOpen: boolean;
  /** Reference to the parent menu item element. */
  parentItemRef: React.RefObject<HTMLElement | null>;
  /** Whether the component is mounted. */
  mounted: boolean;
}

export interface UseFlyoutPositionResult {
  /** Calculated position for the flyout menu. */
  position: FlyoutPosition;
  /** Direction the flyout should fly (left or right). */
  direction: "left" | "right";
  /** Reference to the flyout menu element. */
  menuRef: React.RefObject<HTMLDivElement>;
}

/**
 * Hook for calculating flyout menu position.
 *
 * Calculates position and direction for a flyout menu that should overlap
 * its parent menu item. Follows SRP by handling only position calculation.
 * Follows IOC by accepting refs and state as inputs.
 *
 * Parameters
 * ----------
 * options : UseFlyoutPositionOptions
 *     Configuration including open state, parent ref, and mounted state.
 *
 * Returns
 * -------
 * UseFlyoutPositionResult
 *     Position, direction, and menu ref.
 */
export function useFlyoutPosition({
  isOpen,
  parentItemRef,
  mounted,
}: UseFlyoutPositionOptions): UseFlyoutPositionResult {
  const [position, setPosition] = useState<FlyoutPosition>({ top: 0 });
  const [direction, setDirection] = useState<"left" | "right">("right");
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen || !parentItemRef.current || !mounted) {
      return;
    }

    const updatePosition = () => {
      if (!parentItemRef.current || !menuRef.current) {
        return;
      }

      const parentRect = parentItemRef.current.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const spaceOnRight = viewportWidth - parentRect.right;
      const spaceOnLeft = parentRect.left;

      // Determine direction based on available space
      const shouldFlyLeft =
        spaceOnRight < FLYOUT_MENU_WIDTH && spaceOnLeft > FLYOUT_MENU_WIDTH;
      const flyDirection = shouldFlyLeft ? "left" : "right";

      setDirection(flyDirection);

      if (flyDirection === "right") {
        setPosition({
          top: parentRect.top,
          left: parentRect.right - FLYOUT_OVERLAP,
        });
      } else {
        setPosition({
          top: parentRect.top,
          right: viewportWidth - parentRect.left - FLYOUT_OVERLAP,
        });
      }
    };

    updatePosition();
    window.addEventListener("scroll", updatePosition, true);
    window.addEventListener("resize", updatePosition);

    return () => {
      window.removeEventListener("scroll", updatePosition, true);
      window.removeEventListener("resize", updatePosition);
    };
  }, [isOpen, parentItemRef, mounted]);

  return { position, direction, menuRef };
}
