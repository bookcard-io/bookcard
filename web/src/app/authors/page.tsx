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

import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { AuthorMergeModal } from "@/components/authors/AuthorMergeModal";
import { AuthorSelectionBar } from "@/components/authors/AuthorSelectionBar";
import { AuthorsGrid } from "@/components/authors/AuthorsGrid";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageLayout } from "@/components/layout/PageLayout";
import { LibraryFilterBar } from "@/components/library/LibraryFilterBar";
import { AddBooksButton } from "@/components/library/widgets/AddBooksButton";
import {
  SelectedAuthorsProvider,
  useSelectedAuthors,
} from "@/contexts/SelectedAuthorsContext";
import { useAuthorsViewData } from "@/hooks/useAuthorsViewData";
import { useBookUpload } from "@/hooks/useBookUpload";

const SCROLL_POSITION_KEY = "authors-scroll-position";

/**
 * Authors page content component.
 *
 * Displays a grid of authors with their information.
 */
function AuthorsPageContent() {
  const pathname = usePathname();
  const bookUpload = useBookUpload();
  const { selectedCount, selectedAuthorIds, clearSelection } =
    useSelectedAuthors();
  const [isMergeModalOpen, setIsMergeModalOpen] = useState(false);
  const [filterType, setFilterType] = useState<"all" | "unmatched">("all");
  const { authors, total, hasMore } = useAuthorsViewData({
    pageSize: 20,
    filterType,
  });
  const scrollRestoredRef = useRef(false);
  const isNavigatingAwayRef = useRef(false);

  const handleMerge = () => {
    if (selectedCount >= 2) {
      setIsMergeModalOpen(true);
    }
  };

  const handleDelete = () => {
    // No-op for now
  };

  const handleCloseMergeModal = () => {
    setIsMergeModalOpen(false);
  };

  // Filter handler
  const handleFilterTypeChange = (newFilterType: "all" | "unmatched") => {
    setFilterType(newFilterType);
    // Clear selection when filter changes
    clearSelection();
  };

  const handleViewTypeChange = () => {
    // No-op
  };

  const handleSortByChange = () => {
    // No-op
  };

  const handleSortOrderChange = () => {
    // No-op
  };

  // Save scroll position before navigating away
  useEffect(() => {
    const scrollContainer = document.querySelector(
      '[data-page-scroll-container="true"]',
    ) as HTMLElement | null;

    if (!scrollContainer) {
      return;
    }

    const handleBeforeUnload = () => {
      if (pathname === "/authors" && !isNavigatingAwayRef.current) {
        try {
          sessionStorage.setItem(
            SCROLL_POSITION_KEY,
            String(scrollContainer.scrollTop),
          );
        } catch {
          // Ignore storage errors
        }
      }
    };

    // Save scroll position on scroll (debounced)
    let scrollTimeout: NodeJS.Timeout;
    const handleScroll = () => {
      if (pathname === "/authors" && !isNavigatingAwayRef.current) {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
          try {
            sessionStorage.setItem(
              SCROLL_POSITION_KEY,
              String(scrollContainer.scrollTop),
            );
          } catch {
            // Ignore storage errors
          }
        }, 100);
      }
    };

    scrollContainer.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      clearTimeout(scrollTimeout);
      scrollContainer.removeEventListener("scroll", handleScroll);
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [pathname]);

  // Restore scroll position when returning to the page
  useEffect(() => {
    if (pathname !== "/authors" || scrollRestoredRef.current) {
      return;
    }

    // Wait for authors to be loaded before restoring scroll
    if (authors.length === 0) {
      return;
    }

    const scrollContainer = document.querySelector(
      '[data-page-scroll-container="true"]',
    ) as HTMLElement | null;

    if (!scrollContainer) {
      return;
    }

    // Wait for content to be rendered before restoring scroll
    const restoreScroll = () => {
      try {
        const savedPosition = sessionStorage.getItem(SCROLL_POSITION_KEY);
        if (savedPosition !== null) {
          const scrollTop = parseFloat(savedPosition);
          if (!Number.isNaN(scrollTop) && scrollTop >= 0) {
            // Use requestAnimationFrame to ensure DOM is ready
            requestAnimationFrame(() => {
              scrollContainer.scrollTop = scrollTop;
              scrollRestoredRef.current = true;
            });
          }
        }
      } catch {
        // Ignore storage errors
      }
    };

    // Try to restore with multiple attempts to handle virtualizer initialization
    restoreScroll();
    const timeoutIds = [
      setTimeout(restoreScroll, 100),
      setTimeout(restoreScroll, 300),
      setTimeout(restoreScroll, 500),
    ];

    return () => {
      for (const id of timeoutIds) {
        clearTimeout(id);
      }
    };
  }, [pathname, authors.length]);

  // Reset scroll restoration flag when filter changes
  useEffect(() => {
    if (filterType !== undefined) {
      scrollRestoredRef.current = false;
    }
  }, [filterType]);

  // Track navigation away to prevent saving scroll position during navigation
  useEffect(() => {
    if (pathname === "/authors") {
      isNavigatingAwayRef.current = false;
    } else {
      isNavigatingAwayRef.current = true;
    }
  }, [pathname]);

  return (
    <>
      <PageHeader title="Authors">
        <div className="flex items-center gap-3">
          <AddBooksButton
            fileInputRef={bookUpload.fileInputRef}
            onFileChange={bookUpload.handleFileChange}
            accept={bookUpload.accept}
            isUploading={bookUpload.isUploading}
          />
        </div>
      </PageHeader>
      <div className="relative flex-1 pb-8">
        {selectedCount > 0 && (
          <AuthorSelectionBar
            selectedCount={selectedCount}
            onMerge={handleMerge}
            onDelete={handleDelete}
            onDeselectAll={clearSelection}
          />
        )}
        <LibraryFilterBar
          total={total}
          currentCount={authors.length}
          hasMore={hasMore}
          filterType={filterType}
          onFilterTypeChange={handleFilterTypeChange}
          onViewTypeChange={handleViewTypeChange}
          onSortByChange={handleSortByChange}
          onSortOrderChange={handleSortOrderChange}
        />
        <div className="pt-6">
          <AuthorsGrid filterType={filterType} />
        </div>
      </div>
      {isMergeModalOpen && (
        <AuthorMergeModal
          authorIds={Array.from(selectedAuthorIds)}
          onClose={handleCloseMergeModal}
        />
      )}
    </>
  );
}

/**
 * Authors page.
 *
 * Uses PageLayout for consistent sidebar and context provider setup.
 * Standard action bar buttons (Profile, Admin) are automatically included
 * via the HeaderActionBarButtons component in PageLayout.
 */
export default function AuthorsPage() {
  return (
    <PageLayout>
      <SelectedAuthorsProvider>
        <AuthorsPageContent />
      </SelectedAuthorsProvider>
    </PageLayout>
  );
}
