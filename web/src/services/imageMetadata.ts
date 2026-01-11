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
  ImageDimensionLoader,
  ImageDimensions,
  ImageMetadata,
  ImageMetadataFetcher,
  RawImageMetadata,
} from "@/types/imageMetadata";
import { combineImageMetadata } from "@/utils/imageMetadata";

type FetchLike = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;

/**
 * Fetcher that probes image metadata through an internal proxy endpoint.
 */
export class ProxyImageMetadataFetcher implements ImageMetadataFetcher {
  private readonly endpoint: string;
  private readonly fetchImpl: FetchLike;

  /**
   * Parameters
   * ----------
   * params : object, optional
   *     Constructor parameters.
   * params.endpoint : string, optional
   *     Proxy endpoint to call (default: "/api/metadata/probe-image").
   * params.fetchImpl : callable, optional
   *     Fetch implementation for DI/testing (default: global fetch).
   */
  constructor(params: { endpoint?: string; fetchImpl?: FetchLike } = {}) {
    this.endpoint = params.endpoint ?? "/api/metadata/probe-image";
    this.fetchImpl = params.fetchImpl ?? fetch;
  }

  async fetchMetadata(
    url: string,
    options?: { signal?: AbortSignal },
  ): Promise<RawImageMetadata> {
    const proxyUrl = `${this.endpoint}?url=${encodeURIComponent(url)}`;
    const response = await this.fetchImpl(proxyUrl, {
      signal: options?.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return (await response.json()) as RawImageMetadata;
  }
}

/**
 * Loader that uses the browser Image API to determine natural dimensions.
 */
export class BrowserImageDimensionLoader implements ImageDimensionLoader {
  async loadDimensions(
    url: string,
    options?: { signal?: AbortSignal },
  ): Promise<ImageDimensions | null> {
    return await new Promise<ImageDimensions | null>((resolve) => {
      const img = new Image();
      let settled = false;

      const cleanup = () => {
        img.onload = null;
        img.onerror = null;
        // Clearing src helps cancel/stop some in-flight loads.
        img.src = "";
      };

      const settle = (value: ImageDimensions | null) => {
        if (settled) return;
        settled = true;
        cleanup();
        resolve(value);
      };

      const onAbort = () => settle(null);

      if (options?.signal?.aborted) {
        settle(null);
        return;
      }

      options?.signal?.addEventListener("abort", onAbort, { once: true });

      img.onload = () => {
        options?.signal?.removeEventListener("abort", onAbort);
        settle({ width: img.naturalWidth, height: img.naturalHeight });
      };

      img.onerror = () => {
        options?.signal?.removeEventListener("abort", onAbort);
        settle(null);
      };

      img.src = url;
    });
  }
}

/**
 * Service that combines metadata from a fetcher and a dimension loader.
 */
export class ImageMetadataService {
  constructor(
    private readonly fetcher: ImageMetadataFetcher,
    private readonly loader: ImageDimensionLoader,
  ) {}

  /**
   * Best-effort probe for image metadata.
   *
   * Parameters
   * ----------
   * url : string
   *     Image URL to probe.
   * options : object, optional
   *     Optional abort signal forwarded to dependencies.
   */
  async probe(
    url: string,
    options?: { signal?: AbortSignal },
  ): Promise<ImageMetadata> {
    const [rawResult, dimsResult] = await Promise.allSettled([
      this.fetcher.fetchMetadata(url, options),
      this.loader.loadDimensions(url, options),
    ]);

    const raw: RawImageMetadata =
      rawResult.status === "fulfilled" ? rawResult.value : {};

    const dims: ImageDimensions | null =
      dimsResult.status === "fulfilled" ? dimsResult.value : null;

    return combineImageMetadata(raw, dims);
  }
}
