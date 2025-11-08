"use client";

import { MainContent } from "@/components/library/MainContent";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ActiveLibraryProvider } from "@/contexts/ActiveLibraryContext";
import { SelectedBooksProvider } from "@/contexts/SelectedBooksContext";
import { SidebarProvider } from "@/contexts/SidebarContext";
import styles from "./page.module.scss";

export default function Home() {
  return (
    <ActiveLibraryProvider>
      <SelectedBooksProvider>
        <SidebarProvider>
          <div className={styles.appContainer}>
            <Sidebar />
            <MainContent />
          </div>
        </SidebarProvider>
      </SelectedBooksProvider>
    </ActiveLibraryProvider>
  );
}
