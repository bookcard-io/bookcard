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

import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { ShelfEditModal } from "@/components/shelves/ShelfEditModal";
import { useSelectedShelf } from "@/contexts/SelectedShelfContext";
import { useShelvesContext } from "@/contexts/ShelvesContext";
import { useSidebar } from "@/contexts/SidebarContext";
import { useRecentCreatedShelves } from "@/hooks/useRecentCreatedShelves";
import { BurgerArrowLeft } from "@/icons/BurgerArrowLeft";
import { BurgerArrowRight } from "@/icons/BurgerArrowRight";
import { LibraryBuilding } from "@/icons/LibraryBuilding";
import { LibraryOutline } from "@/icons/LibraryOutline";
import { SharpDevicesFold } from "@/icons/SharpDevicesFold";
import { cn } from "@/libs/utils";
import { createShelf as createShelfApi } from "@/services/shelfService";
import type { Shelf, ShelfCreate, ShelfUpdate } from "@/types/shelf";

interface NavSection {
  title: string;
  items: string[];
}

const navSections: NavSection[] = [
  {
    title: "DEVICES",
    items: ["My Kindle", "iPad Air"],
  },
];

const sectionIcons: Record<
  string,
  React.ComponentType<React.SVGProps<SVGSVGElement>>
> = {
  "MY LIBRARY": LibraryBuilding,
  "MY SHELVES": LibraryOutline,
  DEVICES: SharpDevicesFold,
};

export function Sidebar() {
  const { isCollapsed, setIsCollapsed } = useSidebar();
  const {
    shelves,
    isLoading: shelvesLoading,
    refresh: refreshShelvesContext,
  } = useShelvesContext();
  const { selectedShelfId, setSelectedShelfId } = useSelectedShelf();
  const router = useRouter();
  const pathname = usePathname();
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["MY LIBRARY", "MY SHELVES", "DEVICES"]),
  );
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [shakingShelfId, setShakingShelfId] = useState<number | null>(null);

  // Get top 5 shelves ordered by created_at desc
  const topShelves = useRecentCreatedShelves(shelves);

  const toggleSection = (title: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(title)) {
      newExpanded.delete(title);
    } else {
      newExpanded.add(title);
    }
    setExpandedSections(newExpanded);
  };

  const handleHomeClick = () => {
    setSelectedShelfId(undefined);
    router.push("/");
  };

  const handleShelfClick = (shelfId: number) => {
    // Find the shelf to check book count
    const shelf = shelves.find((s) => s.id === shelfId);

    if (shelf && shelf.book_count === 0) {
      // Empty shelf: trigger shake animation and no-op
      setShakingShelfId(shelfId);
      // Reset shake after animation completes
      setTimeout(() => {
        setShakingShelfId(null);
      }, 500);
      return;
    }

    // Shelf has books: proceed with normal behavior
    setSelectedShelfId(shelfId);
  };

  const handleAddShelfClick = () => {
    // Navigate to home page and activate Shelves tab
    router.push("/?tab=shelves");
  };

  const handleCreateShelf = async (
    data: ShelfCreate | ShelfUpdate,
  ): Promise<Shelf> => {
    const newShelf = await createShelfApi(data as ShelfCreate);
    setShowCreateModal(false);
    await refreshShelvesContext();
    return newShelf;
  };

  const handleLinkClick = () => {
    // No-op for now
  };

  const handleAdminClick = () => {
    router.push("/admin");
  };

  const isAdminActive = pathname === "/admin";

  return (
    <aside
      className={cn(
        "fixed top-0 left-0 z-[1000] flex h-screen w-[var(--sidebar-width)] flex-col overflow-hidden bg-[var(--color-surface-a10)] text-[var(--color-surface-a50)] transition-[width] duration-300 ease-in-out",
        isCollapsed && "w-16",
      )}
    >
      <div className="flex min-h-16 items-center justify-between border-[var(--color-surface-a20)] border-b p-4">
        <div className="flex flex-1 items-center gap-3">
          <img
            src="/logo.svg"
            alt="Fundamental Logo"
            width={24}
            height={24}
            className="h-6 min-h-6 w-6 min-w-6 shrink-0"
          />
          {!isCollapsed && (
            <span className="whitespace-nowrap font-medium text-[var(--color-text-a0)] text-lg">
              Fundamental
            </span>
          )}
        </div>
        <button
          type="button"
          className="flex cursor-pointer items-center justify-center rounded border-0 bg-transparent p-1 text-[var(--color-surface-a50)] transition-colors duration-200 hover:bg-[var(--color-surface-a20)]"
          onClick={() => setIsCollapsed(!isCollapsed)}
          aria-label="Toggle sidebar"
        >
          {isCollapsed ? (
            <BurgerArrowRight className="h-5 w-5" aria-hidden="true" />
          ) : (
            <BurgerArrowLeft className="h-5 w-5" aria-hidden="true" />
          )}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto py-4">
        {/* MY LIBRARY Section */}
        <div className="mb-2">
          <button
            type="button"
            className="flex w-full cursor-pointer items-center justify-between border-0 bg-transparent px-4 py-3 text-left font-semibold text-[var(--color-surface-a50)] text-xs uppercase tracking-[0.5px] transition-colors duration-200 hover:bg-[var(--color-surface-a20)]"
            onClick={() => toggleSection("MY LIBRARY")}
          >
            {LibraryBuilding && (
              <LibraryBuilding
                className="mr-3 h-[18px] w-[18px] shrink-0 text-[var(--color-surface-a50)]"
                aria-hidden="true"
              />
            )}
            {!isCollapsed && <span className="flex-1">MY LIBRARY</span>}
            {!isCollapsed && (
              <i
                className={cn(
                  "pi shrink-0 text-sm",
                  expandedSections.has("MY LIBRARY")
                    ? "pi-chevron-up"
                    : "pi-chevron-down",
                )}
                aria-hidden="true"
              />
            )}
          </button>
          {expandedSections.has("MY LIBRARY") && !isCollapsed && (
            <ul className="m-0 list-none p-0">
              <li>
                <button
                  type="button"
                  onClick={handleHomeClick}
                  className="block w-[calc(100%-32px)] cursor-pointer rounded border-0 bg-transparent py-2.5 pr-4 pl-[46px] text-left text-[var(--color-text-a30)] text-sm no-underline transition-colors duration-200 hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a10)]"
                >
                  Home
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={handleLinkClick}
                  className="block w-[calc(100%-32px)] cursor-pointer rounded border-0 bg-transparent py-2.5 pr-4 pl-[46px] text-left text-[var(--color-text-a30)] text-sm no-underline transition-colors duration-200 hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a10)]"
                >
                  Authors
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={handleLinkClick}
                  className="block w-[calc(100%-32px)] cursor-pointer rounded border-0 bg-transparent py-2.5 pr-4 pl-[46px] text-left text-[var(--color-text-a30)] text-sm no-underline transition-colors duration-200 hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a10)]"
                >
                  Series
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={handleLinkClick}
                  className="block w-[calc(100%-32px)] cursor-pointer rounded border-0 bg-transparent py-2.5 pr-4 pl-[46px] text-left text-[var(--color-text-a30)] text-sm no-underline transition-colors duration-200 hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a10)]"
                >
                  Genres
                </button>
              </li>
              <li>
                <button
                  type="button"
                  onClick={handleLinkClick}
                  className="block w-[calc(100%-32px)] cursor-pointer rounded border-0 bg-transparent py-2.5 pr-4 pl-[46px] text-left text-[var(--color-text-a30)] text-sm no-underline transition-colors duration-200 hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a10)]"
                >
                  Publishers
                </button>
              </li>
            </ul>
          )}
        </div>

        {/* MY SHELVES Section */}
        <div className="mb-2">
          <button
            type="button"
            className="flex w-full cursor-pointer items-center justify-between border-0 bg-transparent px-4 py-3 text-left font-semibold text-[var(--color-surface-a50)] text-xs uppercase tracking-[0.5px] transition-colors duration-200 hover:bg-[var(--color-surface-a20)]"
            onClick={() => toggleSection("MY SHELVES")}
          >
            {LibraryOutline && (
              <LibraryOutline
                className="mr-3 h-[18px] w-[18px] shrink-0 text-[var(--color-surface-a50)]"
                aria-hidden="true"
              />
            )}
            {!isCollapsed && <span className="flex-1">MY SHELVES</span>}
            {!isCollapsed && (
              <i
                className={cn(
                  "pi shrink-0 text-sm",
                  expandedSections.has("MY SHELVES")
                    ? "pi-chevron-up"
                    : "pi-chevron-down",
                )}
                aria-hidden="true"
              />
            )}
          </button>
          {expandedSections.has("MY SHELVES") && !isCollapsed && (
            <ul className="m-0 list-none p-0">
              {shelvesLoading ? (
                <li className="px-[46px] py-2.5 text-[var(--color-text-a30)] text-sm">
                  Loading...
                </li>
              ) : topShelves.length === 0 ? (
                <li className="px-[46px] py-2.5 text-[var(--color-text-a30)] text-sm">
                  No shelves yet
                </li>
              ) : (
                topShelves.map((shelf) => (
                  <li key={shelf.id}>
                    <button
                      type="button"
                      onClick={() => handleShelfClick(shelf.id)}
                      className={cn(
                        "block w-[calc(100%-32px)] cursor-pointer rounded border-0 bg-transparent py-2.5 pr-4 pl-[46px] text-left text-[var(--color-text-a30)] text-sm no-underline transition-colors duration-200 hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a10)]",
                        selectedShelfId === shelf.id &&
                          "bg-[var(--color-surface-a20)] text-[var(--color-text-a10)]",
                        shakingShelfId === shelf.id &&
                          "animate-[shake_0.5s_ease-in-out]",
                      )}
                    >
                      {shelf.name}
                    </button>
                  </li>
                ))
              )}
              <li>
                <button
                  type="button"
                  onClick={handleAddShelfClick}
                  className="block w-[calc(100%-32px)] cursor-pointer rounded border-0 bg-transparent py-2.5 pr-4 pl-[46px] text-left text-[var(--color-text-a30)] text-sm no-underline transition-colors duration-200 hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a10)]"
                >
                  Manage shelves
                </button>
              </li>
            </ul>
          )}
        </div>

        {/* Other Sections */}
        {navSections.map((section) => {
          const IconComponent = sectionIcons[section.title];
          return (
            <div key={section.title} className="mb-2">
              <button
                type="button"
                className="flex w-full cursor-pointer items-center justify-between border-0 bg-transparent px-4 py-3 text-left font-semibold text-[var(--color-surface-a50)] text-xs uppercase tracking-[0.5px] transition-colors duration-200 hover:bg-[var(--color-surface-a20)]"
                onClick={() => toggleSection(section.title)}
              >
                {IconComponent && (
                  <IconComponent
                    className="mr-3 h-[18px] w-[18px] shrink-0 text-[var(--color-surface-a50)]"
                    aria-hidden="true"
                  />
                )}
                {!isCollapsed && (
                  <span className="flex-1">{section.title}</span>
                )}
                {!isCollapsed && (
                  <i
                    className={cn(
                      "pi shrink-0 text-sm",
                      expandedSections.has(section.title)
                        ? "pi-chevron-up"
                        : "pi-chevron-down",
                    )}
                    aria-hidden="true"
                  />
                )}
              </button>
              {expandedSections.has(section.title) && !isCollapsed && (
                <ul className="m-0 list-none p-0">
                  {section.items.map((item) => (
                    <li key={item}>
                      <button
                        type="button"
                        onClick={handleLinkClick}
                        className="block w-[calc(100%-32px)] cursor-pointer rounded border-0 bg-transparent py-2.5 pr-4 pl-[46px] text-left text-[var(--color-text-a30)] text-sm no-underline transition-colors duration-200 hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a10)]"
                      >
                        {item}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      </nav>

      <div className="border-[var(--color-surface-a20)] border-t p-4">
        <button
          type="button"
          onClick={handleAdminClick}
          className={cn(
            "flex w-full cursor-pointer items-center gap-3 rounded border-0 bg-transparent p-2 text-[var(--color-surface-a50)] text-sm no-underline transition-colors duration-200 hover:bg-[var(--color-surface-a20)]",
            isAdminActive &&
              "bg-[var(--color-surface-a20)] text-[var(--color-primary-a20)]",
          )}
          aria-label="Admin Settings"
        >
          <i className="pi pi-cog"></i>
          {!isCollapsed && <span>Admin Settings</span>}
        </button>
      </div>

      {showCreateModal && (
        <ShelfEditModal
          shelf={null}
          onClose={() => setShowCreateModal(false)}
          onSave={handleCreateShelf}
        />
      )}
    </aside>
  );
}
