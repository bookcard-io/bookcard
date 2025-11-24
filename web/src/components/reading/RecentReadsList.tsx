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

import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { useBook } from "@/hooks/useBook";
import { useRecentReads } from "@/hooks/useRecentReads";
import { cn } from "@/libs/utils";
import { ReadingProgressIndicator } from "./ReadingProgressIndicator";

export interface RecentReadsListProps {
  /** Maximum number of recent reads to display (default: 10). */
  limit?: number;
  /** Optional className. */
  className?: string;
  /** Display mode: 'grid' or 'list'. */
  mode?: "grid" | "list";
}

/**
 * Recent reads list component.
 *
 * Displays a grid or list of recently read books.
 * Shows book cover, title, progress, and last read date.
 * For dedicated reading page or sidebar.
 * Follows SRP by focusing solely on recent reads display.
 *
 * Parameters
 * ----------
 * props : RecentReadsListProps
 *     Component props including limit and display mode.
 */
export function RecentReadsList({
  limit = 10,
  className,
  mode = "grid",
}: RecentReadsListProps) {
  const router = useRouter();
  const { reads, isLoading, error } = useRecentReads({ limit });

  const handleBookClick = useCallback(
    (bookId: number) => {
      router.push(`/books/${bookId}/view`);
    },
    [router],
  );

  if (isLoading) {
    return (
      <div className={cn("flex items-center justify-center p-4", className)}>
        <span className="text-sm text-text-a40">Loading recent reads...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("flex items-center justify-center p-4", className)}>
        <span className="text-danger-a10 text-sm">Error: {error}</span>
      </div>
    );
  }

  if (reads.length === 0) {
    return (
      <div className={cn("flex items-center justify-center p-4", className)}>
        <span className="text-sm text-text-a40">No recent reads yet.</span>
      </div>
    );
  }

  if (mode === "list") {
    return (
      <div className={cn("flex flex-col gap-2", className)}>
        {reads.map((read) => (
          <RecentReadListItem
            key={read.id}
            read={read}
            onClick={() => handleBookClick(read.book_id)}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4",
        className,
      )}
    >
      {reads.map((read) => (
        <RecentReadGridItem
          key={read.id}
          read={read}
          onClick={() => handleBookClick(read.book_id)}
        />
      ))}
    </div>
  );
}

interface RecentReadItemProps {
  read: {
    book_id: number;
    progress: number;
    updated_at: string;
    format: string;
  };
  onClick: () => void;
}

function RecentReadListItem({ read, onClick }: RecentReadItemProps) {
  const { book, isLoading } = useBook({
    bookId: read.book_id,
    enabled: true,
    full: false,
  });

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return "Today";
    }
    if (diffDays === 1) {
      return "Yesterday";
    }
    if (diffDays < 7) {
      return `${diffDays} days ago`;
    }
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  if (isLoading || !book) {
    return (
      <div className="flex items-center gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-3">
        <div className="h-16 w-12 animate-pulse rounded bg-surface-a20" />
        <div className="flex-1">
          <div className="mb-2 h-4 w-32 animate-pulse rounded bg-surface-a20" />
          <ReadingProgressIndicator progress={read.progress} size="small" />
        </div>
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-3 text-left transition-all hover:bg-surface-a10"
    >
      <img
        src={book.thumbnail_url || "/placeholder-book.png"}
        alt={book.title}
        className="h-16 w-12 rounded object-cover"
      />
      <div className="flex-1">
        <h4 className="mb-1 line-clamp-1 font-medium text-sm text-text-a0">
          {book.title}
        </h4>
        <ReadingProgressIndicator progress={read.progress} size="small" />
        <span className="mt-1 text-text-a40 text-xs">
          Last read: {formatDate(read.updated_at)}
        </span>
      </div>
    </button>
  );
}

function RecentReadGridItem({ read, onClick }: RecentReadItemProps) {
  const { book, isLoading } = useBook({
    bookId: read.book_id,
    enabled: true,
    full: false,
  });

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return "Today";
    }
    if (diffDays === 1) {
      return "Yesterday";
    }
    if (diffDays < 7) {
      return `${diffDays} days ago`;
    }
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  if (isLoading || !book) {
    return (
      <div className="flex flex-col gap-2">
        <div className="aspect-[2/3] w-full animate-pulse rounded bg-surface-a20" />
        <div className="h-4 w-24 animate-pulse rounded bg-surface-a20" />
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className="group flex flex-col gap-2 text-left transition-all"
    >
      <div className="relative aspect-[2/3] w-full overflow-hidden rounded">
        <img
          src={book.thumbnail_url || "/placeholder-book.png"}
          alt={book.title}
          className="h-full w-full object-cover transition-transform group-hover:scale-105"
        />
        <div className="absolute right-0 bottom-0 left-0 bg-gradient-to-t from-black/60 to-transparent p-2">
          <ReadingProgressIndicator progress={read.progress} size="small" />
        </div>
      </div>
      <div className="flex flex-col gap-1">
        <h4 className="line-clamp-2 font-medium text-sm text-text-a0">
          {book.title}
        </h4>
        <span className="text-text-a40 text-xs">
          {formatDate(read.updated_at)}
        </span>
      </div>
    </button>
  );
}
