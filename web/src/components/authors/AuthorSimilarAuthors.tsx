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
import { useMemo } from "react";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { useAuthors } from "@/hooks/useAuthors";
import { cn } from "@/libs/utils";
import type { AuthorWithMetadata } from "@/types/author";

export interface AuthorSimilarAuthorsProps {
  /** Current author data. */
  author: AuthorWithMetadata;
  /** List of similar authors. */
  similarAuthors?: AuthorWithMetadata[];
}

/**
 * Author similar authors section component.
 *
 * Displays a grid of similar authors.
 * Uses fake data for now - in the future, this could use OpenLibrary API
 * or recommendation algorithms.
 * Follows SRP by focusing solely on similar authors grid presentation.
 *
 * Parameters
 * ----------
 * props : AuthorSimilarAuthorsProps
 *     Component props including current author and similar authors.
 */
export function AuthorSimilarAuthors({
  author,
  similarAuthors,
}: AuthorSimilarAuthorsProps) {
  const router = useRouter();
  const { authors: allAuthors } = useAuthors();

  // Get similar authors - use provided similar authors or fallback to other authors
  const authorsToShow = useMemo(() => {
    if (similarAuthors && similarAuthors.length > 0) {
      return similarAuthors;
    }

    // Fallback: get all authors except current one, limit to 6
    return allAuthors
      .filter((a) => {
        // Exclude current author by key or name
        if (author.key && a.key) {
          return a.key !== author.key;
        }
        return a.name !== author.name;
      })
      .slice(0, 6);
  }, [author, similarAuthors, allAuthors]);

  if (authorsToShow.length === 0) {
    return null;
  }

  const handleAuthorClick = (authorKey: string) => {
    const authorId = authorKey.replace("/authors/", "");
    router.push(`/authors/${authorId}`);
  };

  return (
    <div className="flex flex-col gap-4">
      <h2 className="m-0 font-bold text-[var(--color-text-a0)] text-xl">
        Similar Authors
      </h2>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-10">
        {authorsToShow.map((similarAuthor) => (
          <button
            key={similarAuthor.key || similarAuthor.name}
            type="button"
            onClick={() =>
              handleAuthorClick(
                similarAuthor.key || encodeURIComponent(similarAuthor.name),
              )
            }
            className={cn(
              "group flex flex-col gap-3 rounded-md border-2 border-transparent bg-gradient-to-b from-surface-a0 to-surface-a10 p-4 text-left transition-[transform,box-shadow,border-color] duration-200 ease-out",
              "hover:-translate-y-0.5 hover:shadow-card-hover",
              "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
              "focus:not-focus-visible:outline-none focus:outline-none",
            )}
            aria-label={`View ${similarAuthor.name}`}
          >
            {/* Author Photo */}
            <div className="relative aspect-square w-full overflow-hidden rounded-md">
              {similarAuthor.photo_url ? (
                <ImageWithLoading
                  src={similarAuthor.photo_url}
                  alt={`Photo of ${similarAuthor.name}`}
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
                {similarAuthor.name}
              </h3>
              {similarAuthor.location && (
                <p className="m-0 truncate text-[var(--color-text-a30)] text-xs">
                  {similarAuthor.location}
                </p>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
