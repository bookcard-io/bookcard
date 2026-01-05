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

import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { HeaderActionBar } from "@/components/layout/HeaderActionBar";
import { SearchInput } from "@/components/library/widgets/SearchInput";
import { trackedBookSearchSuggestionsService } from "@/services/trackedBookSearchSuggestionsService";
import type { SearchSuggestion } from "@/types/search";

interface TrackedBooksHeaderProps {
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  onSubmit?: (query: string) => void;
  children?: ReactNode;
}

export function TrackedBooksHeader({
  searchQuery,
  onSearchChange,
  onSubmit,
  children,
}: TrackedBooksHeaderProps) {
  const router = useRouter();

  const handleSuggestionClick = (suggestion: SearchSuggestion) => {
    if (suggestion.type === "BOOK") {
      router.push(`/tracked-books/${suggestion.id}`);
    } else {
      // For other types, fallback to search behavior
      onSearchChange?.(suggestion.name);
      onSubmit?.(suggestion.name);
    }
  };

  return (
    <header className="grid grid-cols-[minmax(0,1fr)_auto] grid-rows-2 gap-x-4 gap-y-2 px-8 pt-6 pb-4 sm:flex sm:items-center sm:justify-between">
      <div className="col-span-1 row-span-2 m-0 w-full max-w-xl">
        <SearchInput
          placeholder="Search tracked books..."
          value={searchQuery}
          onChange={onSearchChange}
          onSubmit={onSubmit}
          suggestionsService={trackedBookSearchSuggestionsService}
          onSuggestionClick={handleSuggestionClick}
        />
      </div>
      <div className="col-start-2 row-span-2 row-start-1 flex flex-col items-end gap-2 sm:col-auto sm:row-auto sm:flex-row sm:items-center sm:gap-3">
        {children}
        <HeaderActionBar />
      </div>
    </header>
  );
}
