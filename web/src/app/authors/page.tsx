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

import { AuthorsGrid } from "@/components/authors/AuthorsGrid";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageLayout } from "@/components/layout/PageLayout";
import { AddBooksButton } from "@/components/library/widgets/AddBooksButton";
import { useBookUpload } from "@/hooks/useBookUpload";

/**
 * Authors page content component.
 *
 * Displays a grid of authors with their information.
 */
function AuthorsPageContent() {
  const bookUpload = useBookUpload();

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
      <div className="flex-1 overflow-y-auto pb-8">
        <AuthorsGrid />
      </div>
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
      <AuthorsPageContent />
    </PageLayout>
  );
}
