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

import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { InterfaceContentBook2LibraryContentBooksBookShelfStack } from "@/icons/Shelf";
import { getShelfCoverUrlWithCacheBuster } from "@/utils/shelves";

export interface ShelfCardCoverProps {
  /** Shelf name for alt text. */
  shelfName: string;
  /** Shelf ID for cover picture URL. */
  shelfId: number;
  /** Whether shelf has a cover picture. */
  hasCoverPicture: boolean;
}

/**
 * Shelf card cover image component.
 *
 * Displays shelf cover thumbnail or placeholder with Shelf icon.
 * Follows SRP by focusing solely on cover display.
 * Follows DRY by reusing ImageWithLoading component.
 */
export function ShelfCardCover({
  shelfName,
  shelfId,
  hasCoverPicture,
}: ShelfCardCoverProps) {
  return (
    <div className="relative aspect-[2/3] w-full overflow-hidden">
      {hasCoverPicture ? (
        <ImageWithLoading
          src={getShelfCoverUrlWithCacheBuster(shelfId)}
          alt={`Cover for ${shelfName}`}
          width={200}
          height={300}
          className="h-full w-full object-cover"
          containerClassName="w-full h-full"
          unoptimized
        />
      ) : (
        <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-surface-a20 to-surface-a10">
          <div className="absolute inset-0 bg-surface-a30/50 backdrop-blur-sm" />
          <div className="relative z-10 flex items-center justify-center">
            <InterfaceContentBook2LibraryContentBooksBookShelfStack className="h-16 w-16 text-text-a40" />
          </div>
        </div>
      )}
    </div>
  );
}
