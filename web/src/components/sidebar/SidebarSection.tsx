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

import type { ReactNode } from "react";
import { cn } from "@/libs/utils";

export interface SidebarSectionProps {
  /** Section title. */
  title: string;
  /** Icon component to display. */
  icon?: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  /** Whether the sidebar is collapsed. */
  isCollapsed: boolean;
  /** Whether the section is expanded. */
  isExpanded: boolean;
  /** Callback when section header is clicked. */
  onToggle: () => void;
  /** Callback when icon is clicked while sidebar is collapsed. */
  onIconClick?: () => void;
  /** Child components to render when expanded. */
  children: ReactNode;
}

/**
 * Generic sidebar section component.
 *
 * Displays a collapsible section with header and content.
 * Follows SRP by handling only section rendering.
 * Follows IOC by accepting all behavior via props.
 * Follows DRY by providing reusable section pattern.
 *
 * Parameters
 * ----------
 * props : SidebarSectionProps
 *     Component props.
 */
export function SidebarSection({
  title,
  icon: Icon,
  isCollapsed,
  isExpanded,
  onToggle,
  onIconClick,
  children,
}: SidebarSectionProps) {
  const handleIconClick = (e: React.MouseEvent) => {
    if (isCollapsed && onIconClick) {
      e.stopPropagation();
      onIconClick();
    }
  };

  return (
    <div className="mb-2">
      <button
        type="button"
        className={cn(
          "flex w-full cursor-pointer items-center justify-between",
          "border-0 bg-transparent px-4 py-3",
          "text-left font-semibold text-[var(--color-surface-a50)] text-xs uppercase tracking-[0.5px]",
          "transition-colors duration-200",
          "hover:bg-[var(--color-surface-a20)]",
        )}
        onClick={onToggle}
      >
        {Icon && (
          <Icon
            className="mr-3 h-[18px] w-[18px] shrink-0 text-[var(--color-surface-a50)]"
            aria-hidden="true"
            onClick={handleIconClick}
          />
        )}
        {!isCollapsed && <span className="flex-1">{title}</span>}
        {!isCollapsed && (
          <i
            className={cn(
              "pi shrink-0 text-sm",
              isExpanded ? "pi-chevron-up" : "pi-chevron-down",
            )}
            aria-hidden="true"
          />
        )}
      </button>
      {isExpanded && !isCollapsed && (
        <ul className="m-0 list-none p-0">{children}</ul>
      )}
    </div>
  );
}
