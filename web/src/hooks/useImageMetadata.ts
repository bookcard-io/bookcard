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

import { useEffect, useMemo, useState } from "react";
import {
  BrowserImageDimensionLoader,
  ImageMetadataService,
  ProxyImageMetadataFetcher,
} from "@/services/imageMetadata";
import type {
  ImageDimensionLoader,
  ImageMetadata,
  ImageMetadataFetcher,
} from "@/types/imageMetadata";
import { EMPTY_IMAGE_METADATA } from "@/utils/imageMetadata";

export {
  BrowserImageDimensionLoader,
  ImageMetadataService,
  ProxyImageMetadataFetcher,
} from "@/services/imageMetadata";
export type {
  ImageDimensionLoader,
  ImageDimensions,
  ImageMetadata,
  ImageMetadataFetcher,
  RawImageMetadata,
} from "@/types/imageMetadata";

/**
 * Options for configuring `useImageMetadata`.
 */
export interface UseImageMetadataOptions {
  fetcher?: ImageMetadataFetcher;
  loader?: ImageDimensionLoader;
  service?: ImageMetadataService;
}

const DEFAULT_FETCHER = new ProxyImageMetadataFetcher();
const DEFAULT_LOADER = new BrowserImageDimensionLoader();
const DEFAULT_SERVICE = new ImageMetadataService(
  DEFAULT_FETCHER,
  DEFAULT_LOADER,
);

/**
 * Hook to probe image metadata (size, dimensions, type) in a best-effort manner.
 *
 * This hook is intentionally thin:
 * - Infrastructure concerns are delegated to injected dependencies.
 * - Orchestration lives in `ImageMetadataService`.
 *
 * Parameters
 * ----------
 * url : string or null or undefined
 *     Image URL to probe.
 * options : UseImageMetadataOptions, optional
 *     Dependency overrides for testability and extensibility.
 *
 * Returns
 * -------
 * ImageMetadata
 *     Normalized metadata object (fields null if unavailable).
 */
export function useImageMetadata(
  url: string | null | undefined,
  options: UseImageMetadataOptions = {},
): ImageMetadata {
  const [metadata, setMetadata] = useState<ImageMetadata>(EMPTY_IMAGE_METADATA);

  const service = useMemo(() => {
    if (options.service) return options.service;

    // Keep the default service stable unless overrides are provided.
    if (!options.fetcher && !options.loader) return DEFAULT_SERVICE;

    return new ImageMetadataService(
      options.fetcher ?? DEFAULT_FETCHER,
      options.loader ?? DEFAULT_LOADER,
    );
  }, [options.fetcher, options.loader, options.service]);

  useEffect(() => {
    if (!url) {
      setMetadata(EMPTY_IMAGE_METADATA);
      return;
    }

    let isActive = true;
    const abortController = new AbortController();

    // Avoid showing stale metadata when URL changes.
    setMetadata(EMPTY_IMAGE_METADATA);

    void (async () => {
      const result = await service.probe(url, {
        signal: abortController.signal,
      });
      if (isActive && !abortController.signal.aborted) {
        setMetadata(result);
      }
    })();

    return () => {
      isActive = false;
      abortController.abort();
    };
  }, [service, url]);

  return metadata;
}
