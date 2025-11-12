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
