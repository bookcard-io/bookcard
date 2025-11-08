"use client";

import { useState } from "react";
import { BooksGrid } from "@/components/library/BooksGrid";
import { LibraryHeader } from "@/components/library/LibraryHeader";
import { SearchWidgetBar } from "@/components/library/SearchWidgetBar";
import type { ViewMode } from "@/components/library/widgets/ViewModeButtons";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ActiveLibraryProvider } from "@/contexts/ActiveLibraryContext";
import { SelectedBooksProvider } from "@/contexts/SelectedBooksContext";
import { SidebarProvider, useSidebar } from "@/contexts/SidebarContext";
import styles from "./page.module.scss";

function MainContent() {
  const { isCollapsed } = useSidebar();
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy] = useState<
    "timestamp" | "pubdate" | "title" | "author_sort" | "series_index"
  >("timestamp");
  const [sortOrder] = useState<"asc" | "desc">("desc");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
  };

  const handleSearchSubmit = (value: string) => {
    setSearchQuery(value);
  };

  const handleBookClick = (book: { id: number }) => {
    // TODO: Navigate to book detail page
    console.log("Book clicked:", book.id);
  };

  return (
    <main
      className={`${styles.mainContent} ${isCollapsed ? styles.collapsed : ""}`}
    >
      <div className={styles.contentWrapper}>
        <LibraryHeader />
        <SearchWidgetBar
          searchValue={searchQuery}
          onSearchChange={handleSearchChange}
          onSearchSubmit={handleSearchSubmit}
          activeViewMode={viewMode}
          onViewModeChange={setViewMode}
        />
        {viewMode === "grid" && (
          <BooksGrid
            searchQuery={searchQuery}
            sortBy={sortBy}
            sortOrder={sortOrder}
            onBookClick={handleBookClick}
          />
        )}
      </div>
    </main>
  );
}

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
