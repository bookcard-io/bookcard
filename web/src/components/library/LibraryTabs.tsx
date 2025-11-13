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

export type LibraryTabId = "library" | "shelves";

export interface LibraryTabsProps {
  /**
   * Currently active tab ID.
   */
  activeTab: LibraryTabId;
  /**
   * Callback fired when a tab is clicked.
   */
  onTabChange: (tabId: LibraryTabId) => void;
}

/**
 * Plex-style tab navigation component for Library and Shelves views.
 *
 * Displays centered tab links with primary color accent for active state.
 * Follows SRP by handling only tab navigation UI.
 */
export function LibraryTabs({ activeTab, onTabChange }: LibraryTabsProps) {
  const tabs: { id: LibraryTabId; label: string }[] = [
    { id: "library", label: "Library" },
    { id: "shelves", label: "Shelves" },
  ];

  return (
    <div className="flex justify-center">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          className={cn(
            "relative cursor-pointer border-0 border-transparent border-b-2 bg-transparent px-6 py-3 font-semibold text-sm transition-[color,border-color] duration-200",
            activeTab === tab.id
              ? "border-b-[var(--color-primary-a0)] text-[var(--color-primary-a0)]"
              : "text-text-a30 hover:text-text-a10",
          )}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
