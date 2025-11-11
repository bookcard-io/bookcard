"use client";

import { useMemo } from "react";
import { useHeaderActionBar } from "@/contexts/HeaderActionBarContext";

/**
 * Defines the intended order of buttons in the header action bar.
 * Buttons are sorted by this order, with buttons not in this list appearing last.
 */
const BUTTON_ORDER: readonly string[] = ["admin", "profile"] as const;

/**
 * Header action bar component.
 *
 * Displays buttons registered via the HeaderActionBarContext.
 * Buttons are sorted according to the intended order defined in BUTTON_ORDER.
 * Follows SRP by only handling rendering of registered buttons.
 * Follows IOC by using context for dependency injection.
 */
export function HeaderActionBar() {
  const { buttons } = useHeaderActionBar();

  const sortedButtons = useMemo(() => {
    if (buttons.length === 0) {
      return [];
    }

    // Sort buttons by their position in BUTTON_ORDER
    return [...buttons].sort((a, b) => {
      const indexA = BUTTON_ORDER.indexOf(a.id);
      const indexB = BUTTON_ORDER.indexOf(b.id);

      // If both buttons are in the order list, sort by their position
      if (indexA >= 0 && indexB >= 0) {
        return indexA - indexB;
      }
      // If only A is in the order list, A comes first
      if (indexA >= 0) {
        return -1;
      }
      // If only B is in the order list, B comes first
      if (indexB >= 0) {
        return 1;
      }
      // If neither is in the order list, maintain original order
      return 0;
    });
  }, [buttons]);

  if (sortedButtons.length === 0) {
    return null;
  }

  return (
    <div className="flex shrink-0 items-center gap-3">
      {sortedButtons.map((button) => (
        <div key={button.id}>{button.element}</div>
      ))}
    </div>
  );
}
