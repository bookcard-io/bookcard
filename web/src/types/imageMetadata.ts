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

/**
 * Image dimensions in pixels.
 */
export interface ImageDimensions {
  width: number;
  height: number;
}

/**
 * Normalized image metadata for UI display.
 */
export interface ImageMetadata {
  sizeKiB: number | null;
  dimensions: ImageDimensions | null;
  extension: string | null;
  mimeType: string | null;
}

/**
 * Raw metadata returned by a probe endpoint.
 */
export interface RawImageMetadata {
  size?: number;
  extension?: string;
  mimeType?: string;
}

/**
 * Dependency for fetching image metadata from an external source.
 */
export interface ImageMetadataFetcher {
  /**
   * Fetch metadata for an image URL.
   *
   * Parameters
   * ----------
   * url : string
   *     Image URL to probe.
   * options : object, optional
   *     Optional abort signal for request cancellation.
   */
  fetchMetadata(
    url: string,
    options?: { signal?: AbortSignal },
  ): Promise<RawImageMetadata>;
}

/**
 * Dependency for loading image dimensions (width/height).
 */
export interface ImageDimensionLoader {
  /**
   * Load image natural dimensions.
   *
   * Parameters
   * ----------
   * url : string
   *     Image URL to load.
   * options : object, optional
   *     Optional abort signal for cancellation.
   */
  loadDimensions(
    url: string,
    options?: { signal?: AbortSignal },
  ): Promise<ImageDimensions | null>;
}
