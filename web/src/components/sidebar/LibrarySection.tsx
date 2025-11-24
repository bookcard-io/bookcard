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

import { useState } from "react";
import { LibraryBuilding } from "@/icons/LibraryBuilding";
import { cn } from "@/libs/utils";
import { SidebarNavItem } from "./SidebarNavItem";

export interface LibrarySectionProps {
  /** Whether the sidebar is collapsed. */
  isCollapsed: boolean;
  /** Whether the section is expanded. */
  isExpanded: boolean;
  /** Callback when section header is clicked. */
  onToggle: () => void;
  /** Callback when home is clicked. */
  onHomeClick: () => void;
  /** Callback when authors is clicked. */
  onAuthorsClick: () => void;
  /** Callback when reading is clicked. */
  onReadingClick: () => void;
  /** Callback when icon is clicked while sidebar is collapsed. */
  onIconClick?: () => void;
}

/**
 * Library section component for sidebar.
 *
 * Displays library navigation items (Home, Authors, Series, etc.).
 * Follows SRP by handling only library section rendering.
 * Follows IOC by accepting all behavior via props.
 *
 * Parameters
 * ----------
 * props : LibrarySectionProps
 *     Component props.
 */
export function LibrarySection({
  isCollapsed,
  isExpanded,
  onToggle,
  onHomeClick,
  onAuthorsClick,
  onReadingClick,
  onIconClick,
}: LibrarySectionProps) {
  const [showMoreView, setShowMoreView] = useState(false);

  const handleMoreClick = () => {
    setShowMoreView(true);
  };

  const handleBackClick = () => {
    setShowMoreView(false);
  };

  const handleIconClick = (e: React.MouseEvent) => {
    if (isCollapsed && onIconClick) {
      e.stopPropagation();
      onIconClick();
    }
  };

  return (
    <div className="mb-2">
      {/* Fixed header */}
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
        <LibraryBuilding
          className="mr-3 h-[18px] w-[18px] shrink-0 text-[var(--color-surface-a50)]"
          aria-hidden="true"
          onClick={handleIconClick}
        />
        {!isCollapsed && <span className="flex-1">MY LIBRARY</span>}
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

      {/* Sliding content */}
      {isExpanded && !isCollapsed && (
        <div className="relative overflow-hidden">
          <div
            className="flex transition-transform duration-300 ease-in-out"
            style={{
              width: "200%",
              transform: showMoreView ? "translateX(-50%)" : "translateX(0)",
            }}
          >
            {/* Main view */}
            <ul className="m-0 w-1/2 shrink-0 list-none p-0">
              <SidebarNavItem label="Home" onClick={onHomeClick} />
              <SidebarNavItem label="Authors" onClick={onAuthorsClick} />
              <SidebarNavItem label="Reading" onClick={onReadingClick} />
              <SidebarNavItem label="Genres" onClick={() => {}} />
              <li>
                <button
                  type="button"
                  onClick={handleMoreClick}
                  className="block w-[calc(100%-32px)] cursor-pointer rounded border-0 bg-transparent py-2.5 pr-4 pl-[46px] text-left text-[var(--color-text-a30)] text-sm no-underline transition-colors duration-200 hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a10)]"
                >
                  <div className="flex items-center gap-2">
                    <span className="truncate">More</span>
                    <i className="pi pi-chevron-right flex-shrink-0 text-xs" />
                  </div>
                </button>
              </li>
            </ul>

            {/* More view */}
            <ul className="m-0 w-1/2 shrink-0 list-none p-0">
              <SidebarNavItem label="Series" onClick={() => {}} />
              <SidebarNavItem label="Publishers" onClick={() => {}} />
              <li>
                <button
                  type="button"
                  onClick={handleBackClick}
                  className="block w-[calc(100%-32px)] cursor-pointer rounded border-0 bg-transparent py-2.5 pr-4 pl-[46px] text-left text-[var(--color-text-a30)] text-sm no-underline transition-colors duration-200 hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a10)]"
                >
                  <div className="flex items-center gap-2">
                    <i className="pi pi-chevron-left flex-shrink-0 text-xs" />
                    <span className="truncate">Back</span>
                  </div>
                </button>
              </li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
