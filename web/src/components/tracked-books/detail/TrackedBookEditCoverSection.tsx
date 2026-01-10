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

import { useCallback, useEffect, useRef, useState } from "react";
import { FaBook } from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { TextInput } from "@/components/forms/TextInput";
import type { TrackedBook } from "@/types/trackedBook";

export interface TrackedBookEditCoverSectionProps {
  /** Current tracked book being edited. */
  book: TrackedBook;
  /** Current cover url from the form (for live preview). */
  coverUrl?: string | null;
  /** Callback to set the cover URL on the form. */
  onCoverUrlSet: (url: string | null) => void;
  /** Whether updates are in progress (disable interactions). */
  isUpdating?: boolean;
}

/**
 * Cover section for tracked book edit modal.
 *
 * Shows a left-column cover preview, similar to the book edit modal layout.
 */
export function TrackedBookEditCoverSection({
  book,
  coverUrl,
  onCoverUrlSet,
  isUpdating = false,
}: TrackedBookEditCoverSectionProps) {
  const [displayUrl, setDisplayUrl] = useState<string | null>(
    coverUrl ?? book.cover_url ?? null,
  );
  const [isUrlInputVisible, setIsUrlInputVisible] = useState(false);
  const [urlDraft, setUrlDraft] = useState("");
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    setDisplayUrl(coverUrl ?? book.cover_url ?? null);
  }, [coverUrl, book.cover_url]);

  useEffect(() => {
    if (isUrlInputVisible) {
      setUrlDraft(coverUrl ?? "");
      // Focus after render
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [isUrlInputVisible, coverUrl]);

  const applyUrl = useCallback(() => {
    const trimmed = urlDraft.trim();
    onCoverUrlSet(trimmed ? trimmed : null);
    setIsUrlInputVisible(false);
  }, [onCoverUrlSet, urlDraft]);

  const handleSetFromUrlClick = useCallback(() => {
    if (isUrlInputVisible) {
      if (urlDraft.trim()) {
        applyUrl();
      } else {
        setIsUrlInputVisible(false);
      }
      return;
    }
    setIsUrlInputVisible(true);
  }, [isUrlInputVisible, urlDraft, applyUrl]);

  return (
    <div className="flex flex-col">
      <div className="flex flex-col gap-4">
        <div className="w-full">
          <div className="aspect-[2/3] w-full overflow-hidden rounded-md shadow-lg">
            {displayUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={displayUrl}
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
        <div className="flex flex-col gap-2">
          <Button
            type="button"
            variant="ghost"
            size="small"
            onClick={handleSetFromUrlClick}
            disabled={isUpdating}
            className="!border-primary-a20 !text-primary-a20 hover:!text-primary-a20 focus:!shadow-none w-full justify-start rounded-md hover:border-primary-a10 hover:bg-surface-a20 focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span
              className="pi pi-link mr-2 text-primary-a20"
              aria-hidden="true"
            />
            Set cover art from URL
          </Button>

          {isUrlInputVisible && (
            <div className="mt-2">
              <TextInput
                ref={inputRef}
                id="tracked-cover-url-input"
                value={urlDraft}
                onChange={(e) => setUrlDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    applyUrl();
                  }
                  if (e.key === "Escape") {
                    e.preventDefault();
                    setIsUrlInputVisible(false);
                  }
                }}
                placeholder="Paste URL and press Enter"
                disabled={isUpdating}
                autoFocus
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
