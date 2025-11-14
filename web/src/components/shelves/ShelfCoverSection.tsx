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

import { Button } from "@/components/forms/Button";
import { getShelfCoverPictureUrl } from "@/services/shelfService";
import type { Shelf } from "@/types/shelf";
import { IMAGE_ACCEPT_ATTRIBUTE } from "@/utils/imageValidation";

export interface ShelfCoverSectionProps {
  /** Shelf (for edit mode). */
  shelf: Shelf | null;
  /** Whether component is in edit mode. */
  isEditMode: boolean;
  /** Whether cover deletion is staged. */
  isCoverDeleteStaged: boolean;
  /** Cover preview URL (for new files). */
  coverPreviewUrl: string | null;
  /** Cover validation error message. */
  coverError: string | null;
  /** File input ref. */
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  /** Whether operations are in progress. */
  isSaving: boolean;
  /** Handle file input change. */
  onCoverFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  /** Clear cover file. */
  onClearCoverFile: () => void;
  /** Stage cover deletion. */
  onCoverDelete: () => void;
  /** Cancel staged deletion. */
  onCancelDelete: () => void;
}

/**
 * Shelf cover picture section component.
 *
 * Displays cover picture upload/delete UI for shelf forms.
 * Follows SRP by focusing solely on cover picture presentation.
 * Follows IOC by accepting callbacks for all interactions.
 *
 * Parameters
 * ----------
 * props : ShelfCoverSectionProps
 *     Component props.
 */
export function ShelfCoverSection({
  shelf,
  isEditMode,
  isCoverDeleteStaged,
  coverPreviewUrl,
  coverError,
  fileInputRef,
  isSaving,
  onCoverFileChange,
  onClearCoverFile,
  onCoverDelete,
  onCancelDelete,
}: ShelfCoverSectionProps) {
  return (
    <div className="space-y-4">
      <div className="font-medium text-sm text-text-a10">
        Cover picture (optional)
      </div>
      {isEditMode && shelf && shelf.cover_picture && !isCoverDeleteStaged ? (
        <div className="space-y-4">
          <img
            src={getShelfCoverPictureUrl(shelf.id)}
            alt={`${shelf.name} cover`}
            className="h-32 w-32 rounded-lg object-cover"
          />
          <div className="flex gap-2">
            <Button
              type="button"
              variant="secondary"
              size="medium"
              onClick={onCoverDelete}
              disabled={isSaving}
            >
              Delete Cover
            </Button>
          </div>
        </div>
      ) : isEditMode && isCoverDeleteStaged ? (
        <div className="space-y-4">
          <div className="flex h-32 w-32 items-center justify-center rounded-lg border-2 border-surface-a30 border-dashed bg-surface-a20">
            <span className="text-sm text-text-a40">Cover will be deleted</span>
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="secondary"
              size="medium"
              onClick={onCancelDelete}
              disabled={isSaving}
            >
              Cancel Delete
            </Button>
          </div>
        </div>
      ) : coverPreviewUrl ? (
        <div className="space-y-4">
          <img
            src={coverPreviewUrl}
            alt="Cover preview"
            className="h-32 w-32 rounded-lg object-cover"
          />
          <div className="flex gap-2">
            <Button
              type="button"
              variant="secondary"
              size="medium"
              onClick={onClearCoverFile}
              disabled={isSaving}
            >
              Clear
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <input
            ref={fileInputRef}
            type="file"
            accept={IMAGE_ACCEPT_ATTRIBUTE}
            onChange={onCoverFileChange}
            className="block w-full rounded-lg border border-surface-a20 bg-surface-a0 px-4 py-3 font-inherit text-base text-text-a0 leading-normal transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s] file:mr-4 file:cursor-pointer file:rounded file:border-0 file:bg-surface-a20 file:px-4 file:py-2 file:font-semibold file:text-sm file:text-text-a0 hover:file:bg-surface-a30 focus:border-primary-a0 focus:bg-surface-a10 focus:shadow-[var(--shadow-focus-ring)] focus:outline-none hover:not(:focus):border-surface-a30"
          />
        </div>
      )}
      {coverError && (
        <p className="text-danger-a10 text-sm leading-normal" role="alert">
          {coverError}
        </p>
      )}
    </div>
  );
}
