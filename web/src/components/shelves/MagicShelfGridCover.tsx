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
import type { ShelfCoverGridLayout } from "@/hooks/useShelfCover";
import { cn } from "@/libs/utils";

export interface MagicShelfGridCoverProps {
  /** Book cover URLs used to render the grid (typically up to 4). */
  coverUrls: string[];
  /** Shelf name for alt text. */
  shelfName: string;
  /** Grid layout hint computed from cover count. */
  gridLayout: ShelfCoverGridLayout;
}

/**
 * Grid cover preview for Magic Shelves.
 *
 * Renders 1-4 book covers in a responsive grid. Extracted from `ShelfCard` to
 * keep presentation logic cohesive and reusable (SRP/DRY).
 */
export function MagicShelfGridCover({
  coverUrls,
  shelfName,
  gridLayout,
}: MagicShelfGridCoverProps) {
  const gridClasses: Record<ShelfCoverGridLayout, string> = {
    one: "grid grid-cols-1 grid-rows-1",
    two: "grid grid-cols-1 grid-rows-2",
    three: "grid grid-cols-2 grid-rows-2",
    four: "grid grid-cols-2 grid-rows-2",
  };

  return (
    <div className="relative aspect-[2/3] w-full overflow-hidden">
      <div
        className={cn(
          "h-full w-full overflow-hidden bg-gradient-to-br from-surface-a20 to-surface-a10",
          gridClasses[gridLayout],
        )}
      >
        {coverUrls.map((url, idx) => (
          <GridCoverImage
            // urls are unique per book id; stable key preferred for react list
            key={url}
            url={url}
            index={idx}
            shelfName={shelfName}
            isThirdInThree={gridLayout === "three" && idx === 2}
          />
        ))}
      </div>
    </div>
  );
}

interface GridCoverImageProps {
  url: string;
  index: number;
  shelfName: string;
  isThirdInThree: boolean;
}

function GridCoverImage({
  url,
  index,
  shelfName,
  isThirdInThree,
}: GridCoverImageProps) {
  return (
    <div
      className={cn(
        "relative h-full w-full overflow-hidden",
        isThirdInThree && "col-span-2",
      )}
    >
      <ImageWithLoading
        src={url}
        alt={`Cover preview ${index + 1} for ${shelfName}`}
        width={200}
        height={300}
        className="h-full w-full object-cover"
        containerClassName="w-full h-full"
        unoptimized
      />
      <div className="absolute inset-0 ring-1 ring-surface-a0/20" />
    </div>
  );
}
