"use client";

import { useRouter } from "next/navigation";
import { use } from "react";
import { PageLayout } from "@/components/layout/PageLayout";
import { BookDetailView } from "@/components/tracked-books/detail/BookDetailView";
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
      <BookDetailView book={book} />
    </PageLayout>
  );
}
