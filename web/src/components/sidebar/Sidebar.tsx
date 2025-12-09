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

import { useState } from "react";
import { ShelfEditModal } from "@/components/shelves/ShelfEditModal";
import { useSelectedShelf } from "@/contexts/SelectedShelfContext";
import { useShelvesContext } from "@/contexts/ShelvesContext";
import { useSidebar } from "@/contexts/SidebarContext";
import { useUser } from "@/contexts/UserContext";
import { useDeviceActions } from "@/hooks/useDeviceActions";
import { useRecentCreatedShelves } from "@/hooks/useRecentCreatedShelves";
import { useRecentDevices } from "@/hooks/useRecentDevices";
import { useSidebarNavigation } from "@/hooks/useSidebarNavigation";
import { useSidebarScroll } from "@/hooks/useSidebarScroll";
import { useSidebarSections } from "@/hooks/useSidebarSections";
import { cn } from "@/libs/utils";
import {
  type CreateShelfOptions,
  createShelf as createShelfApi,
} from "@/services/shelfService";
import type { Shelf, ShelfCreate, ShelfUpdate } from "@/types/shelf";
import { LibrarySection } from "./LibrarySection";
import { ShelvesSection } from "./ShelvesSection";
import { SidebarDevicesSection } from "./SidebarDevicesSection";
import { SidebarFooter } from "./SidebarFooter";
import { SidebarHeader } from "./SidebarHeader";
import { SidebarNav } from "./SidebarNav";

/**
 * Main sidebar component.
 *
 * Displays navigation sections for library, shelves, and devices.
 * Follows SRP by orchestrating sidebar composition.
 * Follows SOC by delegating to specialized components and hooks.
 * Follows IOC by using dependency injection via hooks and services.
 * Follows DRY by reusing shared components and hooks.
 */
export function Sidebar() {
  const { isCollapsed, setIsCollapsed } = useSidebar();
  const {
    shelves,
    isLoading: shelvesLoading,
    refresh: refreshShelvesContext,
  } = useShelvesContext();
  const { selectedShelfId, setSelectedShelfId } = useSelectedShelf();
  const { user, canPerformAction } = useUser();
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Hooks for different concerns
  const { expandedSections, toggleSection } = useSidebarSections();
  const { navRef, isScrolling } = useSidebarScroll();
  const {
    navigateHome,
    navigateToAuthors,
    navigateToReading,
    navigateToShelves,
    navigateToAdmin,
    navigateToManageDevices,
    isAdminActive,
  } = useSidebarNavigation();
  const { setDefaultDevice } = useDeviceActions();

  // Get top 3 shelves and devices
  const topShelves = useRecentCreatedShelves(shelves);
  const topDevices = useRecentDevices(user?.ereader_devices, { limit: 3 });

  // Shelf handlers
  const handleShelfClick = (shelfId: number) => {
    setSelectedShelfId(shelfId);
  };

  const handleCreateShelf = async (
    data: ShelfCreate | ShelfUpdate,
    options?: CreateShelfOptions,
  ): Promise<Shelf> => {
    const newShelf = await createShelfApi(data as ShelfCreate, options);
    setShowCreateModal(false);
    await refreshShelvesContext();
    return newShelf;
  };

  return (
    <aside
      className={cn(
        "fixed top-0 left-0 z-[1000] flex h-screen w-[var(--sidebar-width)] flex-col overflow-hidden bg-[var(--color-surface-a10)] text-[var(--color-surface-a50)] transition-[width] duration-300 ease-in-out",
        isCollapsed && "w-16",
      )}
    >
      <SidebarHeader
        isCollapsed={isCollapsed}
        onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
      />

      <SidebarNav isScrolling={isScrolling} navRef={navRef}>
        <LibrarySection
          isCollapsed={isCollapsed}
          isExpanded={expandedSections.has("MY LIBRARY")}
          onToggle={() => toggleSection("MY LIBRARY")}
          onHomeClick={navigateHome}
          onAuthorsClick={navigateToAuthors}
          onReadingClick={navigateToReading}
          onIconClick={navigateHome}
        />

        <ShelvesSection
          isCollapsed={isCollapsed}
          isExpanded={expandedSections.has("MY SHELVES")}
          onToggle={() => toggleSection("MY SHELVES")}
          shelves={topShelves}
          isLoading={shelvesLoading}
          selectedShelfId={selectedShelfId}
          onShelfClick={handleShelfClick}
          onManageShelvesClick={navigateToShelves}
          onIconClick={navigateToShelves}
        />

        <SidebarDevicesSection
          isCollapsed={isCollapsed}
          isExpanded={expandedSections.has("DEVICES")}
          onToggle={() => toggleSection("DEVICES")}
          devices={topDevices}
          onDeviceClick={setDefaultDevice}
          onManageDevicesClick={navigateToManageDevices}
          onIconClick={navigateToManageDevices}
        />
      </SidebarNav>

      <SidebarFooter
        isCollapsed={isCollapsed}
        isAdmin={user?.is_admin ?? false}
        isAdminActive={isAdminActive}
        onAdminClick={navigateToAdmin}
      />

      {showCreateModal && canPerformAction("shelves", "create") && (
        <ShelfEditModal
          shelf={null}
          onClose={() => setShowCreateModal(false)}
          onSave={handleCreateShelf}
        />
      )}
    </aside>
  );
}
