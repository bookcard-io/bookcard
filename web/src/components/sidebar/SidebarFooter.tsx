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

import { cn } from "@/libs/utils";

export interface SidebarFooterProps {
  /** Whether the sidebar is collapsed. */
  isCollapsed: boolean;
  /** Whether the user is an admin. */
  isAdmin: boolean;
  /** Whether admin page is active. */
  isAdminActive: boolean;
  /** Callback when admin button is clicked. */
  onAdminClick: () => void;
}

/**
 * Sidebar footer component.
 *
 * Displays admin settings button.
 * Follows SRP by handling only footer rendering.
 * Follows IOC by accepting all behavior via props.
 *
 * Parameters
 * ----------
 * props : SidebarFooterProps
 *     Component props.
 */
export function SidebarFooter({
  isCollapsed,
  isAdmin,
  isAdminActive,
  onAdminClick,
}: SidebarFooterProps) {
  return (
    <div className="border-[var(--color-surface-a20)] border-t p-4">
      {isAdmin && (
        <button
          type="button"
          onClick={onAdminClick}
          className={cn(
            "flex w-full cursor-pointer items-center gap-3 rounded border-0 bg-transparent p-2 text-[var(--color-text-a30)] text-sm no-underline transition-colors duration-200 hover:bg-[var(--color-surface-a20)]",
            isAdminActive &&
              "bg-[var(--color-surface-a20)] text-[var(--color-primary-a20)]",
          )}
          aria-label="Admin settings"
        >
          <i className="pi pi-wrench"></i>
          {!isCollapsed && <span>Admin settings</span>}
        </button>
      )}
    </div>
  );
}
