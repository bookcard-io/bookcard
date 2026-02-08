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

import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import { cn } from "@/libs/utils";
import { SidebarNavItem } from "./SidebarNavItem";

export interface LibrariesSectionProps {
  /** Whether the sidebar is collapsed. */
  isCollapsed: boolean;
}

/**
 * Sidebar section listing visible libraries for multi-library filtering.
 *
 * Only renders when the user has more than one visible library.
 * Provides an "All Libraries" option and one entry per visible library.
 * The active (ingest target) library is marked with a subtle indicator.
 *
 * Follows SRP by handling only library selector rendering.
 * Follows IOC by reading library state from context.
 *
 * Parameters
 * ----------
 * props : LibrariesSectionProps
 *     Component props.
 */
export function LibrariesSection({ isCollapsed }: LibrariesSectionProps) {
  const {
    visibleLibraries,
    selectedLibraryId,
    setSelectedLibraryId,
    activeLibrary,
  } = useActiveLibrary();

  // Only render when multiple libraries are available
  if (visibleLibraries.length <= 1) {
    return null;
  }

  return (
    <div className="mb-2">
      {/* Section header */}
      <div
        className={cn(
          "flex w-full items-center",
          "px-4 py-3",
          "font-semibold text-[var(--color-surface-a50)] text-xs uppercase tracking-[0.5px]",
        )}
      >
        <i
          className="pi pi-book mr-3 h-[18px] w-[18px] shrink-0 text-[var(--color-surface-a50)]"
          aria-hidden="true"
        />
        {!isCollapsed && <span className="flex-1">LIBRARIES</span>}
      </div>

      {/* Library list */}
      {!isCollapsed && (
        <ul className="m-0 list-none p-0">
          <SidebarNavItem
            label="All Libraries"
            isActive={selectedLibraryId === null}
            onClick={() => setSelectedLibraryId(null)}
          />
          {visibleLibraries.map((lib) => (
            <SidebarNavItem
              key={lib.id}
              label={lib.name}
              isActive={selectedLibraryId === lib.id}
              onClick={() => setSelectedLibraryId(lib.id)}
            >
              {activeLibrary?.id === lib.id && (
                <i
                  className="pi pi-upload shrink-0 text-[0.625rem] text-[var(--color-surface-a40)]"
                  aria-hidden="true"
                  title="Active library (ingest target)"
                />
              )}
            </SidebarNavItem>
          ))}
        </ul>
      )}
    </div>
  );
}
