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

import { DiscoverSection } from "@/components/library/discovery/DiscoverSection";
import { MoreByAuthorSection } from "@/components/library/discovery/MoreByAuthorSection";
import { MoreInGenreSection } from "@/components/library/discovery/MoreInGenreSection";
import { OnThisDaySection } from "@/components/library/discovery/OnThisDaySection";
import { RecentlyAddedSection } from "@/components/library/discovery/RecentlyAddedSection";
import { RecentlyReadSection } from "@/components/library/discovery/RecentlyReadSection";
import { RecentShelvesSection } from "@/components/library/discovery/RecentShelvesSection";
import type { Book } from "@/types/book";

export interface DiscoveryTabProps {
  /** Callback when book is clicked. */
  onBookClick?: (book: Book) => void;
  /** Callback when book edit is requested. */
  onBookEdit?: (bookId: number) => void;
  /** Callback when books data changes (for navigation). */
  onBooksDataChange?: (data: {
    bookIds: number[];
    loadMore?: () => void;
    hasMore?: boolean;
    isLoading: boolean;
  }) => void;
}

/**
 * Discovery tab component.
 *
 * Displays personalized book recommendations and library insights.
 * Follows SRP by delegating to specialized section components.
 * Uses IOC via component composition.
 */
export function DiscoveryTab({
  onBookClick,
  onBookEdit,
  onBooksDataChange,
}: DiscoveryTabProps) {
  return (
    <div className="flex flex-col gap-8 px-8 pt-2 pb-6">
      <RecentlyReadSection
        onBookClick={onBookClick}
        onBookEdit={onBookEdit}
        onBooksDataChange={onBooksDataChange}
      />
      <RecentlyAddedSection
        onBookClick={onBookClick}
        onBookEdit={onBookEdit}
        onBooksDataChange={onBooksDataChange}
      />
      <RecentShelvesSection />
      <OnThisDaySection
        onBookClick={onBookClick}
        onBookEdit={onBookEdit}
        onBooksDataChange={onBooksDataChange}
      />
      <MoreByAuthorSection
        onBookClick={onBookClick}
        onBookEdit={onBookEdit}
        onBooksDataChange={onBooksDataChange}
      />
      <MoreInGenreSection
        onBookClick={onBookClick}
        onBookEdit={onBookEdit}
        onBooksDataChange={onBooksDataChange}
      />
      <DiscoverSection
        onBookClick={onBookClick}
        onBookEdit={onBookEdit}
        onBooksDataChange={onBooksDataChange}
      />
    </div>
  );
}
