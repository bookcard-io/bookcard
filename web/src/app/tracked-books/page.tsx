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

import { useState } from "react";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { PageLayout } from "@/components/layout/PageLayout";
import { EmptyBookState } from "@/components/tracked-books/EmptyBookState";
import { TrackedBookCard } from "@/components/tracked-books/TrackedBookCard";
import { TrackedBooksHeader } from "@/components/tracked-books/TrackedBooksHeader";
import { useTrackedBooks } from "@/hooks/useTrackedBooks";
import type { TrackedBook } from "@/types/trackedBook";

export default function TrackedBooksPage() {
  const { trackedBooks, loading, error, refetch } = useTrackedBooks();
  const [searchQuery, setSearchQuery] = useState("");

  const filteredBooks = trackedBooks.filter((book) => {
    const query = searchQuery.toLowerCase();
    return (
      book.title.toLowerCase().includes(query) ||
      book.author?.toLowerCase().includes(query)
    );
  });

  return (
    <PageLayout>
      <div className="flex h-full flex-col">
        <TrackedBooksHeader
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
        ></TrackedBooksHeader>

        <div className="flex flex-1 flex-col p-4 md:p-8">
          <PageDescription />
          <BookListContent
            books={filteredBooks}
            loading={loading}
            error={error}
            onRetry={refetch}
          />
        </div>
      </div>
    </PageLayout>
  );
}

function PageDescription() {
  return (
    <div className="mb-6">
      <p className="text-gray-500 text-sm dark:text-gray-400">
        Manage your book tracking list
      </p>
    </div>
  );
}

interface BookListContentProps {
  books: TrackedBook[];
  loading: boolean;
  error: Error | null;
  onRetry: () => void;
}

function BookListContent({
  books,
  loading,
  error,
  onRetry,
}: BookListContentProps) {
  if (loading) return <LoadingSpinner />;
  if (error)
    return (
      <ErrorState
        error={error}
        onRetry={onRetry}
        message="Failed to load tracked books"
      />
    );
  if (books.length === 0) return <EmptyBookState />;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {books.map((book) => (
        <TrackedBookCard key={book.id} book={book} />
      ))}
    </div>
  );
}
