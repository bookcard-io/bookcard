"use client";

import { LibraryHeader } from "@/components/library/LibraryHeader";
import { SearchWidgetBar } from "@/components/library/SearchWidgetBar";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { SidebarProvider, useSidebar } from "@/contexts/SidebarContext";
import styles from "./page.module.scss";

function MainContent() {
  const { isCollapsed } = useSidebar();
  return (
    <main
      className={`${styles.mainContent} ${isCollapsed ? styles.collapsed : ""}`}
    >
      <div className={styles.contentWrapper}>
        <LibraryHeader />
        <SearchWidgetBar />
      </div>
    </main>
  );
}

export default function Home() {
  return (
    <SidebarProvider>
      <div className={styles.appContainer}>
        <Sidebar />
        <MainContent />
      </div>
    </SidebarProvider>
  );
}
