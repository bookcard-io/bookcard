"use client";

import { AdminSettings } from "@/components/admin/AdminSettings";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ActiveLibraryProvider } from "@/contexts/ActiveLibraryContext";
import { SidebarProvider, useSidebar } from "@/contexts/SidebarContext";
import { cn } from "@/libs/utils";

function AdminContent() {
  const { isCollapsed } = useSidebar();
  return (
    <main
      className={cn(
        "flex-1 overflow-y-auto bg-surface-a0 transition-[margin-left] duration-300 ease-in-out",
        "ml-0 md:ml-[280px]",
        isCollapsed && "md:ml-16",
      )}
    >
      <AdminSettings />
    </main>
  );
}

export default function AdminPage() {
  return (
    <ActiveLibraryProvider>
      <SidebarProvider>
        <div className="flex h-screen w-full overflow-hidden">
          <Sidebar />
          <AdminContent />
        </div>
      </SidebarProvider>
    </ActiveLibraryProvider>
  );
}
