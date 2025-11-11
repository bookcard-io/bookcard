"use client";

import type { ReactNode } from "react";
import { HeaderActionBarButtons } from "@/components/layout/HeaderActionBarButtons";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ActiveLibraryProvider } from "@/contexts/ActiveLibraryContext";
import { HeaderActionBarProvider } from "@/contexts/HeaderActionBarContext";
import { SidebarProvider, useSidebar } from "@/contexts/SidebarContext";
import { UserProvider } from "@/contexts/UserContext";
import { cn } from "@/libs/utils";

interface PageContentProps {
  children: ReactNode;
}

/**
 * Page content wrapper that handles responsive margins based on sidebar state.
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
        "flex-1 overflow-y-auto bg-surface-a0 transition-[margin-left] duration-300 ease-in-out",
        isCollapsed ? "ml-16" : "ml-[280px]",
      )}
    >
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
        <SidebarProvider>
          <HeaderActionBarProvider>
            <HeaderActionBarButtons />
            <div className="flex h-screen w-full overflow-hidden">
              <Sidebar />
              <PageContent>{children}</PageContent>
            </div>
          </HeaderActionBarProvider>
        </SidebarProvider>
      </ActiveLibraryProvider>
    </UserProvider>
  );
}
