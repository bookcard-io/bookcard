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

import { cn } from "@/libs/utils";

export interface SpreadModeToggleProps {
  /** Whether spread mode is enabled. */
  enabled: boolean;
  /** Callback when spread mode changes. */
  onToggle: (enabled: boolean) => void;
}

/**
 * Spread mode toggle component.
 *
 * Displays a toggle switch for enabling/disabling two-page spread mode.
 * Follows SRP by handling only spread mode toggle UI.
 * Follows IOC by accepting callbacks as props.
 *
 * Parameters
 * ----------
 * props : SpreadModeToggleProps
 *     Component props including enabled state and change handler.
 */
export function SpreadModeToggle({ enabled, onToggle }: SpreadModeToggleProps) {
  return (
    <div className="mb-8">
      <h3 className="mb-4 font-medium text-sm text-text-a0">Spread Mode</h3>
      <div className="flex items-center justify-between">
        <div className="flex flex-col">
          <span className="text-sm text-text-a0">Two-page spreads</span>
          <span className="text-text-a40 text-xs">
            Automatically detect and display two-page spreads
          </span>
        </div>
        <button
          type="button"
          onClick={() => onToggle(!enabled)}
          className={cn(
            "relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-a0 focus:ring-offset-2",
            enabled ? "bg-primary-a0" : "bg-surface-a30",
          )}
          role="switch"
          aria-checked={enabled}
          aria-label="Toggle spread mode"
        >
          <span
            className={cn(
              "inline-block h-4 w-4 transform rounded-full bg-surface-a0 transition-transform",
              enabled ? "translate-x-6" : "translate-x-1",
            )}
          />
        </button>
      </div>
    </div>
  );
}
