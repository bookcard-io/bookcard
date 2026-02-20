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

import { useMemo, useState } from "react";
import { LibraryOutline } from "@/icons/LibraryOutline";
import type { Shelf } from "@/types/shelf";
import { SidebarNavItem } from "./SidebarNavItem";
import { SidebarSection } from "./SidebarSection";

interface LibraryInfo {
  id: number;
  name: string;
}

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
  /** Callback when icon is clicked while sidebar is collapsed. */
  onIconClick?: () => void;
  /** Visible libraries (used for grouping when multiple libraries exist). */
  visibleLibraries?: LibraryInfo[];
}

/**
 * Shelves section component for sidebar.
 *
 * Displays recent shelves grouped by library when the user has multiple
 * visible libraries. Falls back to a flat list for single-library users.
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
  onIconClick,
  visibleLibraries = [],
}: ShelvesSectionProps) {
  const [shakingShelfId, setShakingShelfId] = useState<number | null>(null);

  const shouldGroup = visibleLibraries.length > 1;

  const libraryNameMap = useMemo(() => {
    const map = new Map<number, string>();
    for (const lib of visibleLibraries) {
      map.set(lib.id, lib.name);
    }
    return map;
  }, [visibleLibraries]);

  const groupedShelves = useMemo(() => {
    if (!shouldGroup) return null;
    const groups = new Map<number, Shelf[]>();
    for (const shelf of shelves) {
      const existing = groups.get(shelf.library_id);
      if (existing) {
        existing.push(shelf);
      } else {
        groups.set(shelf.library_id, [shelf]);
      }
    }
    return groups;
  }, [shelves, shouldGroup]);

  const handleShelfClick = (shelfId: number) => {
    const shelf = shelves.find((s) => s.id === shelfId);

    if (shelf && shelf.book_count === 0) {
      setShakingShelfId(shelfId);
      setTimeout(() => {
        setShakingShelfId(null);
      }, 500);
      return;
    }

    onShelfClick(shelfId);
  };

  const renderShelfItem = (shelf: Shelf) => (
    <SidebarNavItem
      key={shelf.id}
      label={shelf.name}
      isActive={selectedShelfId === shelf.id}
      isShaking={shakingShelfId === shelf.id}
      onClick={() => handleShelfClick(shelf.id)}
    />
  );

  const renderContent = () => {
    if (isLoading) {
      return (
        <li className="px-[46px] py-2.5 text-[var(--color-text-a30)] text-sm">
          Loading...
        </li>
      );
    }

    if (shelves.length === 0) {
      return (
        <li className="px-[46px] py-2.5 text-[var(--color-text-a30)] text-sm">
          No shelves yet
        </li>
      );
    }

    if (groupedShelves) {
      return Array.from(groupedShelves.entries()).map(
        ([libraryId, libShelves]) => (
          <li key={libraryId}>
            <span className="block px-[46px] pt-3 pb-1 font-medium text-[0.65rem] text-[var(--color-surface-a40)] uppercase tracking-wider">
              {libraryNameMap.get(libraryId) ?? `Library ${libraryId}`}
            </span>
            <ul className="m-0 list-none p-0">
              {libShelves.map(renderShelfItem)}
            </ul>
          </li>
        ),
      );
    }

    return shelves.map(renderShelfItem);
  };

  return (
    <SidebarSection
      title="MY SHELVES"
      icon={LibraryOutline}
      isCollapsed={isCollapsed}
      isExpanded={isExpanded}
      onToggle={onToggle}
      onIconClick={onIconClick}
    >
      {renderContent()}
      <SidebarNavItem label="Manage shelves" onClick={onManageShelvesClick} />
    </SidebarSection>
  );
}
