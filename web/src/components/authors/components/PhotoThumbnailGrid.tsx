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

import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { cn } from "@/libs/utils";

interface PhotoThumbnailGridProps {
  thumbnails: string[];
  selectedThumbnail: string | null;
  onSelect: (url: string) => void;
  onDelete?: (url: string) => void;
  canDelete?: (url: string) => boolean;
}

/**
 * Component for displaying a grid of thumbnail images.
 *
 * Follows SRP by handling only thumbnail display and selection.
 */
export function PhotoThumbnailGrid({
  thumbnails,
  selectedThumbnail,
  onSelect,
  onDelete,
  canDelete,
}: PhotoThumbnailGridProps) {
  const handleSelect = (url: string) => {
    onSelect(url);
  };

  const handleKeyDown = (
    e: React.KeyboardEvent<HTMLButtonElement>,
    url: string,
  ) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleSelect(url);
    }
  };

  const handleDelete = (
    e: React.MouseEvent | React.KeyboardEvent,
    url: string,
  ) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(url);
    }
  };

  const handleDeleteKeyDown = (
    e: React.KeyboardEvent<HTMLDivElement>,
    url: string,
  ) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleDelete(e, url);
    }
  };

  return (
    <div className="grid w-full grid-cols-[repeat(auto-fill,minmax(100px,1fr))] gap-3">
      {thumbnails.map((url) => {
        const isSelected = selectedThumbnail === url;
        return (
          <button
            key={url}
            type="button"
            className={cn(
              "relative aspect-square cursor-pointer overflow-hidden rounded-md border-2 bg-surface-a10 p-0 transition-colors",
              "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
              isSelected
                ? "border-primary-a0"
                : "border-transparent hover:border-surface-a40",
            )}
            onClick={() => handleSelect(url)}
            onKeyDown={(e) => handleKeyDown(e, url)}
          >
            <ImageWithLoading
              src={url}
              alt="Photo thumbnail"
              width={100}
              height={100}
              className="block h-full w-full object-cover"
              unoptimized
            />
            {isSelected && (
              <div className="absolute top-1 right-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary-a0 font-bold text-white text-xs">
                ✓
              </div>
            )}
            {onDelete && (!canDelete || canDelete(url)) && (
              /* biome-ignore lint/a11y/useSemanticElements: Cannot use <button> here as it would be nested inside the parent <button> element, which is invalid HTML and causes hydration errors. */
              <div
                role="button"
                tabIndex={0}
                onClick={(e) => handleDelete(e, url)}
                onKeyDown={(e) => handleDeleteKeyDown(e, url)}
                className={cn(
                  /* Position */
                  "absolute right-2 bottom-2 z-10",
                  /* Layout */
                  "flex h-6 w-6 items-center justify-center rounded",
                  /* Background */
                  "bg-surface-a20/80 backdrop-blur-sm",
                  /* Interactions */
                  "cursor-pointer transition-colors duration-200",
                  "hover:bg-surface-a30",
                  /* Focus states */
                  "focus:outline-2 focus:outline-primary-a0 focus:outline-offset-2",
                )}
                aria-label="Delete photo"
                title="Delete photo"
              >
                <i
                  className={cn("pi pi-trash text-xs")}
                  style={{ color: "var(--color-danger-a20)" }}
                  aria-hidden="true"
                />
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
