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
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { useAuthors } from "@/hooks/useAuthors";
import { cn } from "@/libs/utils";
import type { AuthorWithMetadata } from "@/types/author";

/**
 * Authors grid component.
 *
 * Displays a grid of author cards.
 * Follows SRP by focusing solely on grid presentation.
 */
export function AuthorsGrid() {
  const router = useRouter();
  const { authors, isLoading, error } = useAuthors();

  const handleAuthorClick = (author: AuthorWithMetadata) => {
    // Use the key if available, otherwise use the name as fallback
    const authorId = author.key
      ? author.key.replace("/authors/", "")
      : encodeURIComponent(author.name);
    router.push(`/authors/${authorId}`);
  };

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-base text-text-a30">
        Loading authors...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-base text-text-a30">
        {error}
      </div>
    );
  }

  if (authors.length === 0) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-base text-text-a30">
        No authors found
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
      {authors.map((author) => (
        <button
          key={author.key || author.name}
          type="button"
          onClick={() => handleAuthorClick(author)}
          className={cn(
            "group flex flex-col gap-3 rounded-md border-2 border-transparent bg-gradient-to-b from-surface-a0 to-surface-a10 p-4 text-left transition-[transform,box-shadow,border-color] duration-200 ease-out",
            "hover:-translate-y-0.5 hover:shadow-card-hover",
            "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
            "focus:not-focus-visible:outline-none focus:outline-none",
          )}
          aria-label={`View ${author.name}`}
        >
          {/* Author Photo */}
          <div className="relative aspect-square w-full overflow-hidden rounded-md">
            {author.photo_url ? (
              <ImageWithLoading
                src={author.photo_url}
                alt={`Photo of ${author.name}`}
                width={200}
                height={200}
                className="h-full w-full object-cover"
                containerClassName="h-full w-full"
                unoptimized
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center bg-surface-a20">
                <i
                  className="pi pi-user text-4xl text-text-a40"
                  aria-hidden="true"
                />
              </div>
            )}
          </div>

          {/* Author Name */}
          <div className="flex min-w-0 flex-col gap-1">
            <h3 className="m-0 truncate font-medium text-[var(--color-text-a0)] text-sm group-hover:text-[var(--color-primary-a0)]">
              {author.name}
            </h3>
            {author.location && (
              <p className="m-0 truncate text-[var(--color-text-a30)] text-xs">
                {author.location}
              </p>
            )}
          </div>
        </button>
      ))}
    </div>
  );
}
