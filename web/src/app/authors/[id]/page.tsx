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
import { useCallback, useEffect, useState } from "react";
import { AuthorDetailView } from "@/components/authors/AuthorDetailView";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageLayout } from "@/components/layout/PageLayout";
import { AddBooksButton } from "@/components/library/widgets/AddBooksButton";
import { SelectedBooksProvider } from "@/contexts/SelectedBooksContext";
import { useAuthor } from "@/hooks/useAuthor";
import { useBookUpload } from "@/hooks/useBookUpload";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import { useModal } from "@/hooks/useModal";

interface AuthorDetailPageProps {
  params: Promise<{ id: string }>;
}

/**
 * Author detail page.
 *
 * Displays comprehensive author information in a full-page view.
 * Similar to Plex artist page layout.
 */
export default function AuthorDetailPage({ params }: AuthorDetailPageProps) {
  const router = useRouter();
  const [authorId, setAuthorId] = useState<string | null>(null);
  const bookUpload = useBookUpload();

  // Initialize author ID from params
  useEffect(() => {
    void params.then((p) => {
      setAuthorId(p.id);
    });
  }, [params]);

  const { author, isLoading, error, refetch, updateAuthor } = useAuthor({
    authorId: authorId || null,
    enabled: authorId !== null,
  });

  const handleBack = useCallback(() => {
    router.push("/authors");
  }, [router]);

  // Handle keyboard navigation
  useKeyboardNavigation({
    onEscape: handleBack,
    enabled: author !== null,
  });

  // Prevent body scroll when modal-like view is open
  useModal(author !== null);

  if (!authorId || isLoading) {
    return (
      <SelectedBooksProvider>
        <PageLayout>
          <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-base text-text-a30">
            Loading author data...
          </div>
        </PageLayout>
      </SelectedBooksProvider>
    );
  }

  if (error || !author) {
    return (
      <SelectedBooksProvider>
        <PageLayout>
          <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-base text-text-a30">
            {error || "Author not found"}
            <button
              type="button"
              onClick={handleBack}
              className="btn-tonal mt-4"
            >
              Back to Authors
            </button>
          </div>
        </PageLayout>
      </SelectedBooksProvider>
    );
  }

  return (
    <SelectedBooksProvider>
      <PageLayout>
        <PageHeader title="Author">
          <div className="flex items-center gap-3">
            <AddBooksButton
              fileInputRef={bookUpload.fileInputRef}
              onFileChange={bookUpload.handleFileChange}
              accept={bookUpload.accept}
              isUploading={bookUpload.isUploading}
            />
          </div>
        </PageHeader>
        <AuthorDetailView
          author={author}
          onBack={handleBack}
          onRefetch={refetch}
          onAuthorUpdate={updateAuthor}
        />
      </PageLayout>
    </SelectedBooksProvider>
  );
}
