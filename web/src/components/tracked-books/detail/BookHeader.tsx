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
import {
  FaBarcode,
  FaBook,
  FaBuilding,
  FaGlobe,
  FaTag,
  FaUser,
} from "react-icons/fa";
import { cn } from "@/libs/utils";
import type { TrackedBook } from "@/types/trackedBook";
import { extractYear } from "@/utils/dateFormatters";
import { BookDescription } from "./BookDescription";
import { BookToolbar } from "./BookToolbar";
import { StatusBadge } from "./StatusBadge";

interface BookHeaderProps {
  book: TrackedBook;
  onSearchClick: () => void;
  onEditClick: () => void;
  onDeleteClick: () => void;
}

const MAX_TAGS = 10;

export function BookHeader({
  book,
  onSearchClick,
  onEditClick,
  onDeleteClick,
}: BookHeaderProps) {
  const [tagsExpanded, setTagsExpanded] = useState(false);
  const uniqueTags = Array.from(new Set(book.tags || []));
  const visibleTags = tagsExpanded ? uniqueTags : uniqueTags.slice(0, MAX_TAGS);

  return (
    <div className="relative z-10 flex flex-col gap-6 border-surface-a20 p-6 md:flex-row md:p-8">
      {/* Poster */}
      <div className="z-10 w-[140px] flex-shrink-0 self-center md:self-start">
        <div className="aspect-[2/3] w-full overflow-hidden rounded-md shadow-lg">
          {book.cover_url ? (
            <img
              src={book.cover_url}
              alt={book.title}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center bg-surface-a30">
              <FaBook className="h-12 w-12 text-text-a40" />
            </div>
          )}
        </div>
      </div>

      {/* Info Column */}
      <div className="z-10 flex min-w-0 flex-1 flex-col justify-between gap-4">
        <div>
          {/* Title & Year */}
          <div className="mb-1 flex flex-wrap items-baseline gap-x-3">
            <h1 className="font-bold text-3xl text-text-a0 md:text-4xl">
              {book.title}
            </h1>
            {book.published_date && (
              <span className="text-text-a30 text-xl">
                {extractYear(book.published_date)}
              </span>
            )}
          </div>

          {/* Subtitle / Path / Details */}
          <div className="mb-4 flex flex-col gap-1 text-sm text-text-a30">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="flex items-center gap-1.5 font-medium text-text-a10">
                <FaUser className="text-text-a40" />
                {book.author}
              </span>
              {book.isbn && (
                <>
                  <span className="text-text-a40">•</span>
                  <span className="flex items-center gap-1.5">
                    <FaBarcode className="text-text-a40" />
                    ISBN: {book.isbn}
                  </span>
                </>
              )}
              {book.publisher && (
                <>
                  <span className="text-text-a40">•</span>
                  <span className="flex items-center gap-1.5">
                    <FaBuilding className="text-text-a40" />
                    {book.publisher}
                  </span>
                </>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs opacity-70">
                /books/{book.author}/{book.title}
              </span>
            </div>
          </div>

          {/* Status, Badges & Tags */}
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <StatusBadge status={book.status} />
            {book.metadata_source_id && (
              <span className="flex items-center gap-1 rounded-md border border-surface-a20 bg-surface-a0 px-2 py-1 text-text-a20 text-xs uppercase tracking-wide">
                <FaGlobe className="text-text-a40" />
                {book.metadata_source_id}
              </span>
            )}
            {book.rating && (
              <span
                className={cn(
                  "flex items-center gap-1 rounded-md border border-surface-a20 bg-surface-a0 px-2 py-1 font-bold text-xs",
                  book.rating >= 80 ? "text-success-a10" : "text-warning-a10",
                )}
              >
                {book.rating}%
              </span>
            )}
            {visibleTags.map((tag) => (
              <span
                key={tag}
                className="flex items-center gap-1 rounded-md bg-surface-a20 px-3 py-1 text-text-a20 text-xs transition-colors hover:bg-surface-a30"
              >
                <FaTag className="text-[10px] opacity-70" />
                {tag}
              </span>
            ))}
            {uniqueTags.length > MAX_TAGS && (
              <button
                type="button"
                onClick={() => setTagsExpanded(!tagsExpanded)}
                className="ml-1 cursor-pointer font-bold text-primary-a0 text-xs hover:text-primary-a10"
              >
                {tagsExpanded ? "Less" : "More"}
              </button>
            )}
          </div>

          {/* Toolbar */}
          <BookToolbar
            onSearchClick={onSearchClick}
            onAutomatedSearchClick={() => {}} // Placeholder
            onEditClick={onEditClick}
            onManualImportClick={() => {}} // Placeholder
            onDeleteClick={onDeleteClick}
          />
        </div>

        {/* Description */}
        <BookDescription description={book.description} />
      </div>
    </div>
  );
}
