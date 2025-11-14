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

import type { ReactNode } from "react";
import { HeaderActionBarButtons } from "@/components/layout/HeaderActionBarButtons";
import { PageLoadingOverlay } from "@/components/layout/PageLoadingOverlay";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ActiveLibraryProvider } from "@/contexts/ActiveLibraryContext";
import { HeaderActionBarProvider } from "@/contexts/HeaderActionBarContext";
import { LibraryLoadingProvider } from "@/contexts/LibraryLoadingContext";
import { SelectedShelfProvider } from "@/contexts/SelectedShelfContext";
import { ShelvesProvider } from "@/contexts/ShelvesContext";
import { SidebarProvider, useSidebar } from "@/contexts/SidebarContext";
import { UserProvider } from "@/contexts/UserContext";
import { cn } from "@/libs/utils";

interface PageContentProps {
  children: ReactNode;
}

/**
 * Page content wrapper that handles responsive margins based on sidebar state.
 *
 * Also hosts the global `PageLoadingOverlay` so that the soft loading spinner
 * is always centered over the main content area, independently of the sidebar.
 *
 * Parameters
 * ----------
 * children : ReactNode
 *     Content to render inside the main element.
 */
function PageContent({ children }: PageContentProps) {
  const { isCollapsed } = useSidebar();
  return (
    <main
      className={cn(
        "relative flex-1 overflow-y-auto bg-surface-a0 transition-[margin-left] duration-300 ease-in-out",
        isCollapsed ? "ml-16" : "ml-[var(--sidebar-width)]",
      )}
    >
      <PageLoadingOverlay />
      {children}
    </main>
  );
}

interface PageLayoutProps {
  children: ReactNode;
}

/**
 * Common page layout component with sidebar and context providers.
 *
 * Provides a consistent layout structure for pages that need:
 * - ActiveLibraryProvider context
 * - SidebarProvider context
 * - Sidebar component
 * - Responsive content area with proper margins
 *
 * Parameters
 * ----------
 * children : ReactNode
 *     Page content to render inside the layout.
 *
 * Examples
 * --------
 * ```tsx
 * <PageLayout>
 *   <YourPageContent />
 * </PageLayout>
 * ```
 */
export function PageLayout({ children }: PageLayoutProps) {
  return (
    <UserProvider>
      <ActiveLibraryProvider>
        <ShelvesProvider>
          <LibraryLoadingProvider>
            <SelectedShelfProvider>
              <SidebarProvider>
                <HeaderActionBarProvider>
                  <HeaderActionBarButtons />
                  <div className="flex h-screen w-full overflow-hidden">
                    <Sidebar />
                    <PageContent>{children}</PageContent>
                  </div>
                </HeaderActionBarProvider>
              </SidebarProvider>
            </SelectedShelfProvider>
          </LibraryLoadingProvider>
        </ShelvesProvider>
      </ActiveLibraryProvider>
    </UserProvider>
  );
}
