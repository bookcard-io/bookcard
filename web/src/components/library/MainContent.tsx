"use client";

import { useState } from "react";
import { BooksGrid } from "@/components/library/BooksGrid";
import { LibraryHeader } from "@/components/library/LibraryHeader";
import { SearchWidgetBar } from "@/components/library/SearchWidgetBar";
import type { ViewMode } from "@/components/library/widgets/ViewModeButtons";
import { useSidebar } from "@/contexts/SidebarContext";
import type { SearchSuggestion } from "@/types/search";
import styles from "./MainContent.module.scss";

/**
 * Main content area for the library view.
 * Handles search, filtering, sorting, and book display.
 */
export function MainContent() {
  const { isCollapsed } = useSidebar();
  // Separate state for input value (what user types) vs filter query (what filters books)
  const [searchInputValue, setSearchInputValue] = useState("");
  const [filterQuery, setFilterQuery] = useState("");
  const [sortBy] = useState<
    "timestamp" | "pubdate" | "title" | "author_sort" | "series_index"
  >("timestamp");
  const [sortOrder] = useState<"asc" | "desc">("desc");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");

  const handleSearchChange = (value: string) => {
    // Update input value but don't filter - only show suggestions
    setSearchInputValue(value);
  };

  const handleSearchSubmit = (value: string) => {
    // When user submits search manually, filter by the submitted value
    setFilterQuery(value);
    setSearchInputValue(value);
  };

  const handleSuggestionClick = (suggestion: SearchSuggestion) => {
    // Filter books by tag, author, or series when suggestion pill is clicked
    if (
      suggestion.type === "TAG" ||
      suggestion.type === "AUTHOR" ||
      suggestion.type === "SERIES"
    ) {
      setFilterQuery(suggestion.name);
      setSearchInputValue(suggestion.name);
    }
    // BOOK type is no-op as requested
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
          searchValue={searchInputValue}
          onSearchChange={handleSearchChange}
          onSearchSubmit={handleSearchSubmit}
          onSuggestionClick={handleSuggestionClick}
          activeViewMode={viewMode}
          onViewModeChange={setViewMode}
        />
        {viewMode === "grid" && (
          <BooksGrid
            searchQuery={filterQuery}
            sortBy={sortBy}
            sortOrder={sortOrder}
            onBookClick={handleBookClick}
          />
        )}
      </div>
    </main>
  );
}
