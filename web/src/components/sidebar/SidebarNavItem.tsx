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

export interface SidebarNavItemProps {
  /** Item label text. */
  label: string;
  /** Whether the item is active/selected. */
  isActive?: boolean;
  /** Whether the item should show shake animation. */
  isShaking?: boolean;
  /** Callback when item is clicked. */
  onClick: () => void;
  /** Optional content to display alongside label (e.g., StatusPill). */
  children?: React.ReactNode;
}

/**
 * Sidebar navigation item component.
 *
 * Displays a clickable navigation item with optional active/shake states.
 * Follows SRP by handling only item rendering.
 * Follows IOC by accepting all behavior via props.
 * Follows DRY by providing reusable item pattern.
 *
 * Parameters
 * ----------
 * props : SidebarNavItemProps
 *     Component props.
 */
export function SidebarNavItem({
  label,
  isActive = false,
  isShaking = false,
  onClick,
  children,
}: SidebarNavItemProps) {
  return (
    <li>
      <button
        type="button"
        onClick={onClick}
        className={cn(
          "block w-[calc(100%-32px)] cursor-pointer rounded border-0 bg-transparent py-2.5 pr-4 pl-[46px] text-left text-[var(--color-text-a30)] text-sm no-underline transition-colors duration-200 hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a10)]",
          isActive &&
            "bg-[var(--color-surface-a20)] text-[var(--color-text-a10)]",
          isShaking && "animate-[shake_0.5s_ease-in-out]",
        )}
      >
        {children ? (
          <div className="flex items-center gap-2">
            <span className="truncate">{label}</span>
            {children}
          </div>
        ) : (
          label
        )}
      </button>
    </li>
  );
}
