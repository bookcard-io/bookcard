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

export interface BookCardCoverProps {
  /** Book title for alt text. */
  title: string;
  /** Thumbnail URL. */
  thumbnailUrl?: string | null;
}

/**
 * Book card cover image component.
 *
 * Displays book cover thumbnail or placeholder.
 * Follows SRP by focusing solely on cover display.
 */
export function BookCardCover({ title, thumbnailUrl }: BookCardCoverProps) {
  return (
    <div className="relative aspect-[2/3] w-full overflow-hidden">
      {thumbnailUrl ? (
        <ImageWithLoading
          src={thumbnailUrl}
          alt={`Cover for ${title}`}
          width={200}
          height={300}
          className="h-full w-full object-cover"
          containerClassName="w-full h-full"
          unoptimized
        />
      ) : (
        <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-surface-a20 to-surface-a10">
          <span className="text-sm text-text-a40 uppercase tracking-[0.5px]">
            No Cover
          </span>
        </div>
      )}
    </div>
  );
}
