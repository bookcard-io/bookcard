"use client";

import { useMemo } from "react";
import { useHeaderActionBar } from "@/contexts/HeaderActionBarContext";
import { compareButtonOrder } from "./utils/buttonSorting";

/**
 * Header action bar component.
 *
 * Displays buttons registered via the HeaderActionBarContext.
 * Buttons are sorted according to the intended order defined in buttonSorting.
 * Follows SRP by only handling rendering of registered buttons.
 * Follows IOC by using context for dependency injection.
 * Follows SOC by delegating sorting logic to a utility function.
 */
export function HeaderActionBar() {
  const { buttons } = useHeaderActionBar();

  const sortedButtons = useMemo(() => {
    if (buttons.length === 0) {
      return [];
    }
    return [...buttons].sort((a, b) => compareButtonOrder(a.id, b.id));
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
