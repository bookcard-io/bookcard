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

import { useRef } from "react";

export interface HeaderTriggerZoneProps {
  /** Whether the header is currently visible. */
  isVisible: boolean;
  /** Handler for mouse enter event. */
  onMouseEnter: () => void;
}

/**
 * Invisible trigger zone for header visibility.
 *
 * Follows SRP by focusing solely on trigger zone rendering.
 * Follows SOC by separating trigger zone from header component.
 *
 * Parameters
 * ----------
 * props : HeaderTriggerZoneProps
 *     Component props including visibility state and handler.
 */
export function HeaderTriggerZone({
  isVisible,
  onMouseEnter,
}: HeaderTriggerZoneProps) {
  const triggerZoneRef = useRef<HTMLButtonElement>(null);

  if (isVisible) {
    return null;
  }

  return (
    <button
      ref={triggerZoneRef}
      onMouseEnter={onMouseEnter}
      type="button"
      className="fixed top-0 right-0 left-0 z-[850] h-8 cursor-default border-0 bg-transparent p-0"
      aria-hidden="true"
      tabIndex={-1}
    />
  );
}
