"use client";

import { AdminSettings } from "@/components/admin/AdminSettings";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ActiveLibraryProvider } from "@/contexts/ActiveLibraryContext";
import { SidebarProvider, useSidebar } from "@/contexts/SidebarContext";
import styles from "./page.module.scss";

function AdminContent() {
  const { isCollapsed } = useSidebar();
  return (
    <main
      className={`${styles.mainContent} ${isCollapsed ? styles.collapsed : ""}`}
    >
      <AdminSettings />
    </main>
  );
}

export default function AdminPage() {
  return (
    <ActiveLibraryProvider>
      <SidebarProvider>
        <div className={styles.appContainer}>
          <Sidebar />
          <AdminContent />
        </div>
      </SidebarProvider>
    </ActiveLibraryProvider>
  );
}
