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
import { LibraryOutline } from "@/icons/LibraryOutline";
import type { Shelf } from "@/types/shelf";
import { SidebarNavItem } from "./SidebarNavItem";
import { SidebarSection } from "./SidebarSection";

export interface ShelvesSectionProps {
  /** Whether the sidebar is collapsed. */
  isCollapsed: boolean;
  /** Whether the section is expanded. */
  isExpanded: boolean;
  /** Callback when section header is clicked. */
  onToggle: () => void;
  /** List of shelves to display. */
  shelves: Shelf[];
  /** Whether shelves are loading. */
  isLoading: boolean;
  /** Currently selected shelf ID. */
  selectedShelfId?: number;
  /** Callback when a shelf is clicked. */
  onShelfClick: (shelfId: number) => void;
  /** Callback when manage shelves is clicked. */
  onManageShelvesClick: () => void;
}

/**
 * Shelves section component for sidebar.
 *
 * Displays recent shelves and manage shelves link.
 * Follows SRP by handling only shelves section rendering.
 * Follows IOC by accepting all behavior via props.
 *
 * Parameters
 * ----------
 * props : ShelvesSectionProps
 *     Component props.
 */
export function ShelvesSection({
  isCollapsed,
  isExpanded,
  onToggle,
  shelves,
  isLoading,
  selectedShelfId,
  onShelfClick,
  onManageShelvesClick,
}: ShelvesSectionProps) {
  const [shakingShelfId, setShakingShelfId] = useState<number | null>(null);

  const handleShelfClick = (shelfId: number) => {
    const shelf = shelves.find((s) => s.id === shelfId);

    if (shelf && shelf.book_count === 0) {
      // Empty shelf: trigger shake animation and no-op
      setShakingShelfId(shelfId);
      setTimeout(() => {
        setShakingShelfId(null);
      }, 500);
      return;
    }

    // Shelf has books: proceed with normal behavior
    onShelfClick(shelfId);
  };

  return (
    <SidebarSection
      title="MY SHELVES"
      icon={LibraryOutline}
      isCollapsed={isCollapsed}
      isExpanded={isExpanded}
      onToggle={onToggle}
    >
      {isLoading ? (
        <li className="px-[46px] py-2.5 text-[var(--color-text-a30)] text-sm">
          Loading...
        </li>
      ) : shelves.length === 0 ? (
        <li className="px-[46px] py-2.5 text-[var(--color-text-a30)] text-sm">
          No shelves yet
        </li>
      ) : (
        shelves.map((shelf) => (
          <SidebarNavItem
            key={shelf.id}
            label={shelf.name}
            isActive={selectedShelfId === shelf.id}
            isShaking={shakingShelfId === shelf.id}
            onClick={() => handleShelfClick(shelf.id)}
          />
        ))
      )}
      <SidebarNavItem label="Manage shelves" onClick={onManageShelvesClick} />
    </SidebarSection>
  );
}
