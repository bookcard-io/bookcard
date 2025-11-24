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

"use client";

import { useCallback } from "react";

export interface ThemeSettingsOverlayProps {
  /** Whether the overlay should be visible. */
  isVisible: boolean;
  /** Callback when overlay is clicked. */
  onClick: () => void;
}

/**
 * Theme settings overlay backdrop component.
 *
 * Provides the backdrop overlay for the settings panel.
 * Follows SRP by handling only overlay rendering.
 * Follows IOC by accepting callbacks as props.
 *
 * Parameters
 * ----------
 * props : ThemeSettingsOverlayProps
 *     Component props including visibility and click handler.
 */
export function ThemeSettingsOverlay({
  isVisible,
  onClick,
}: ThemeSettingsOverlayProps) {
  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        onClick();
      }
    },
    [onClick],
  );

  if (!isVisible) {
    return null;
  }

  return (
    <div
      className="fixed top-[69px] right-0 bottom-0 left-0 z-[750] bg-black/50 transition-opacity duration-300"
      onClick={handleClick}
      role="presentation"
      aria-hidden="true"
    />
  );
}
