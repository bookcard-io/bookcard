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

import type {
  ImageDimensions,
  ImageMetadata,
  RawImageMetadata,
} from "@/types/imageMetadata";

/**
 * Empty image metadata value.
 */
export const EMPTY_IMAGE_METADATA: ImageMetadata = Object.freeze({
  sizeKiB: null,
  dimensions: null,
  extension: null,
  mimeType: null,
});

/**
 * Convert bytes to kibibytes (KiB), rounded to 1 decimal place.
 *
 * Parameters
 * ----------
 * bytes : number
 *     Size in bytes.
 */
export function bytesToKiB(bytes: number): number {
  return Math.round((bytes / 1024) * 10) / 10;
}

/**
 * Format an extension for display.
 *
 * Parameters
 * ----------
 * extension : string or null or undefined
 *     File extension (e.g. "jpg").
 */
export function formatExtension(
  extension: string | null | undefined,
): string | null {
  return extension ? extension.toUpperCase() : null;
}

/**
 * Combine raw probe metadata and dimensions into the normalized UI model.
 *
 * Parameters
 * ----------
 * raw : RawImageMetadata or null or undefined
 *     Raw metadata returned by a probe implementation.
 * dimensions : ImageDimensions or null
 *     Natural dimensions if available.
 */
export function combineImageMetadata(
  raw: RawImageMetadata | null | undefined,
  dimensions: ImageDimensions | null,
): ImageMetadata {
  const size = raw?.size;
  const extension = raw?.extension;
  const mimeType = raw?.mimeType;

  return {
    sizeKiB: typeof size === "number" ? bytesToKiB(size) : null,
    dimensions,
    extension: formatExtension(extension),
    mimeType: mimeType ?? null,
  };
}
