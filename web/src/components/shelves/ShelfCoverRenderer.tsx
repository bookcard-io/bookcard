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

import { MagicShelfGridCover } from "@/components/shelves/MagicShelfGridCover";
import { ShelfCardCover } from "@/components/shelves/ShelfCardCover";
import type { ShelfCoverData } from "@/hooks/useShelfCover";
import type { Shelf } from "@/types/shelf";

export interface ShelfCoverRendererProps {
  /** Shelf for default cover rendering. */
  shelf: Shelf;
  /** Derived cover decision data (typically from `useShelfCover`). */
  coverData: ShelfCoverData;
}

/**
 * Render a shelf cover using a simple cover strategy.
 *
 * Notes
 * -----
 * Centralizes conditional cover rendering so `ShelfCard` remains orchestration-only.
 * This improves OCP (new strategies can be added here without touching `ShelfCard`).
 */
export function ShelfCoverRenderer({
  shelf,
  coverData,
}: ShelfCoverRendererProps) {
  if (coverData.hasCustomCover) {
    return (
      <ShelfCardCover
        shelfName={shelf.name}
        shelfId={shelf.id}
        hasCoverPicture
      />
    );
  }

  if (
    coverData.shouldUseGridCover &&
    coverData.coverUrls.length > 0 &&
    !coverData.error
  ) {
    return (
      <MagicShelfGridCover
        coverUrls={coverData.coverUrls}
        shelfName={shelf.name}
        gridLayout={coverData.gridLayout}
      />
    );
  }

  return (
    <ShelfCardCover
      shelfName={shelf.name}
      shelfId={shelf.id}
      hasCoverPicture={false}
    />
  );
}
