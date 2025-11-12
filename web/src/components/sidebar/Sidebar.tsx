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
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import { useSidebar } from "@/contexts/SidebarContext";
import { BurgerArrowLeft } from "@/icons/BurgerArrowLeft";
import { BurgerArrowRight } from "@/icons/BurgerArrowRight";
import { LibraryBuilding } from "@/icons/LibraryBuilding";
import { LibraryOutline } from "@/icons/LibraryOutline";
import { SharpDevicesFold } from "@/icons/SharpDevicesFold";
import { cn } from "@/libs/utils";

interface NavSection {
  title: string;
  items: string[];
}

const navSections: NavSection[] = [
  {
    title: "MY SHELVES",
    items: ["To-read", "DNF", "Estonian Sci-Fi", "Recommended", "Add shelf"],
  },
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
  const { activeLibrary } = useActiveLibrary();
  const router = useRouter();
  const pathname = usePathname();
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["MY LIBRARY", "MY SHELVES", "DEVICES"]),
  );

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
    router.push("/");
  };

  const handleLibraryMenuClick = () => {
    // Placeholder for now
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
              {activeLibrary && (
                <li>
                  <div className="flex w-[calc(100%-32px)] cursor-pointer items-center justify-between rounded border-0 bg-transparent py-2.5 pr-0 pl-[46px] text-[var(--color-text-a30)] text-sm transition-colors duration-200 hover:bg-[var(--color-surface-a20)]">
                    <span className="flex-1 text-left">
                      {activeLibrary.name}
                    </span>
                    <button
                      type="button"
                      onClick={handleLibraryMenuClick}
                      className="flex items-center justify-center rounded border-0 bg-transparent text-[var(--color-text-a30)] text-base transition-colors duration-200 hover:text-[var(--color-text-a10)]"
                      aria-label="Library options"
                    >
                      <i className="pi pi-ellipsis-v" aria-hidden="true" />
                    </button>
                  </div>
                </li>
              )}
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
    </aside>
  );
}
