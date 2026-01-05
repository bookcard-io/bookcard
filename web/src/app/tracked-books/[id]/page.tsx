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
import { use } from "react";
import { PageLayout } from "@/components/layout/PageLayout";
import { BookDetailView } from "@/components/tracked-books/detail/BookDetailView";
import { TrackedBooksHeader } from "@/components/tracked-books/TrackedBooksHeader";
import { useTrackedBook } from "@/hooks/useTrackedBook";

interface TrackedBookDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function TrackedBookDetailPage({
  params,
}: TrackedBookDetailPageProps) {
  const router = useRouter();
  const resolvedParams = use(params);
  const { book, isLoading, error } = useTrackedBook(resolvedParams.id);

  if (isLoading) {
    return (
      <PageLayout>
        <div className="flex h-full items-center justify-center text-text-a30">
          Loading book details...
        </div>
      </PageLayout>
    );
  }

  if (error || !book) {
    return (
      <PageLayout>
        <div className="flex h-full flex-col items-center justify-center gap-4 text-text-a30">
          <p>{error || "Book not found"}</p>
          <button
            type="button"
            onClick={() => router.back()}
            className="rounded-md bg-surface-tonal-a20 px-4 py-2 text-sm hover:bg-surface-tonal-a30"
          >
            Go Back
          </button>
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout>
      <div className="flex h-full flex-col">
        <TrackedBooksHeader></TrackedBooksHeader>
        <BookDetailView book={book} />
      </div>
    </PageLayout>
  );
}
