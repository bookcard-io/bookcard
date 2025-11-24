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

import { BrandLogo } from "@/components/common/BrandLogo";
import { BurgerArrowLeft } from "@/icons/BurgerArrowLeft";
import { BurgerArrowRight } from "@/icons/BurgerArrowRight";

export interface SidebarHeaderProps {
  /** Whether the sidebar is collapsed. */
  isCollapsed: boolean;
  /** Callback to toggle sidebar collapse state. */
  onToggleCollapse: () => void;
}

/**
 * Sidebar header component.
 *
 * Displays logo and collapse toggle button.
 * Follows SRP by handling only header rendering.
 * Follows IOC by accepting callbacks for all actions.
 *
 * Parameters
 * ----------
 * props : SidebarHeaderProps
 *     Component props.
 */
export function SidebarHeader({
  isCollapsed,
  onToggleCollapse,
}: SidebarHeaderProps) {
  return (
    <div className="flex min-h-16 items-center justify-between border-[var(--color-surface-a20)] border-b p-4">
      <BrandLogo showText={!isCollapsed} className="flex-1" />
      <button
        type="button"
        className="flex cursor-pointer items-center justify-center rounded border-0 bg-transparent p-1 text-[var(--color-surface-a50)] transition-colors duration-200 hover:bg-[var(--color-surface-a20)]"
        onClick={onToggleCollapse}
        aria-label="Toggle sidebar"
      >
        {isCollapsed ? (
          <BurgerArrowRight className="h-5 w-5" aria-hidden="true" />
        ) : (
          <BurgerArrowLeft className="h-5 w-5" aria-hidden="true" />
        )}
      </button>
    </div>
  );
}
