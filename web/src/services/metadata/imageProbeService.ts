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

import type { ImageProbeConfig, ImageProbeResult } from "@/types/imageProbe";
import {
  NotImageError,
  TooLargeError,
  UpstreamError,
} from "@/types/imageProbe";
import {
  extensionFromMimeType,
  isImageMimeType,
  isValidImageExtension,
  normalizeMimeType,
} from "@/utils/metadata/mimeTypes";
import { validateRemoteHttpUrl } from "@/utils/security/ssrf";

type FetchLike = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;

const DEFAULT_CONFIG: ImageProbeConfig = {
  maxSizeBytes: 50 * 1024 * 1024,
  timeoutMs: 10_000,
  allowedSchemes: new Set(["http", "https"]),
  userAgent: "BookCard/1.0",
  followRedirects: false,
};

/**
 * Service that probes remote images for headers-based metadata.
 *
 * It is designed to be safe by default:
 * - Rejects private/local targets (SSRF mitigation)
 * - Does not follow redirects (prevents redirect-based SSRF)
 * - Uses timeouts and avoids downloading full bodies
 */
export class ImageProbeService {
  private readonly config: ImageProbeConfig;
  private readonly fetchImpl: FetchLike;

  /**
   * Parameters
   * ----------
   * params : object, optional
   *     Constructor parameters.
   * params.config : Partial[ImageProbeConfig], optional
   *     Configuration overrides.
   * params.fetchImpl : callable, optional
   *     Fetch implementation for DI/testing (default: global fetch).
   */
  constructor(
    params: { config?: Partial<ImageProbeConfig>; fetchImpl?: FetchLike } = {},
  ) {
    this.config = { ...DEFAULT_CONFIG, ...(params.config ?? {}) };
    this.fetchImpl = params.fetchImpl ?? fetch;
  }

  /**
   * Probe an image URL for size, mime type, and inferred extension.
   *
   * Parameters
   * ----------
   * url : string
   *     Target image URL.
   *
   * Returns
   * -------
   * ImageProbeResult
   *     Probed metadata.
   */
  async probe(url: string): Promise<ImageProbeResult> {
    const parsed = await validateRemoteHttpUrl(url, {
      allowedSchemes: this.config.allowedSchemes,
    });

    // Try HEAD first; some servers don't support it. If it fails, do a minimal GET.
    const head = await this.tryRequest(parsed, { method: "HEAD" });
    if (head.ok) {
      return extractMetadataOrThrow(url, head, this.config.maxSizeBytes);
    }

    // Range GET: avoid large downloads; still gets headers.
    const get = await this.tryRequest(parsed, {
      method: "GET",
      headers: { Range: "bytes=0-0" },
    });

    if (!get.ok) {
      throw new UpstreamError(
        `HTTP ${get.status}: ${get.statusText}`,
        mapStatus(get.status),
      );
    }

    return extractMetadataOrThrow(url, get, this.config.maxSizeBytes);
  }

  private async tryRequest(url: URL, init: RequestInit): Promise<Response> {
    const { controller, timeoutId } = createTimeoutAbortController(
      this.config.timeoutMs,
    );

    try {
      const response = await this.fetchImpl(url, {
        ...init,
        redirect: this.config.followRedirects ? "follow" : "manual",
        signal: controller.signal,
        headers: {
          "User-Agent": this.config.userAgent,
          ...normalizeHeaders(init.headers),
        },
      });

      // Treat redirects as an error when redirects are disabled.
      if (
        !this.config.followRedirects &&
        response.status >= 300 &&
        response.status < 400
      ) {
        throw new UpstreamError("Redirects are not allowed", 400);
      }

      return response;
    } catch (error) {
      if (error instanceof UpstreamError) {
        throw error;
      }
      if (isAbortError(error)) {
        throw new UpstreamError("Upstream request timed out", 504, error);
      }
      throw new UpstreamError("Upstream request failed", 502, error);
    } finally {
      clearTimeout(timeoutId);
    }
  }
}

function extractMetadataOrThrow(
  originalUrl: string,
  response: Response,
  maxSizeBytes: number,
): ImageProbeResult {
  const size = getContentSizeBytes(response);
  if (typeof size === "number" && size > maxSizeBytes) {
    throw new TooLargeError(
      `Image too large: ${size} bytes (max: ${maxSizeBytes})`,
    );
  }

  const contentType = response.headers.get("content-type");
  const mimeType = contentType ? normalizeMimeType(contentType) : null;
  if (mimeType && !isImageMimeType(mimeType)) {
    throw new NotImageError();
  }

  const extensionFromMime = mimeType ? extensionFromMimeType(mimeType) : null;
  const extension =
    extensionFromMime ?? inferImageExtensionFromUrl(originalUrl);

  return {
    size: size ?? null,
    mimeType,
    extension,
  };
}

function getContentSizeBytes(response: Response): number | null {
  const contentRange = response.headers.get("content-range");
  if (contentRange) {
    // Example: "bytes 0-0/12345"
    const slashIndex = contentRange.lastIndexOf("/");
    if (slashIndex !== -1) {
      const totalRaw = contentRange.slice(slashIndex + 1).trim();
      if (totalRaw !== "*") {
        const total = Number(totalRaw);
        if (!Number.isNaN(total)) return total;
      }
    }
  }

  const contentLength = response.headers.get("content-length");
  if (!contentLength) return null;

  const size = Number(contentLength);
  return Number.isNaN(size) ? null : size;
}

function inferImageExtensionFromUrl(url: string): string | null {
  try {
    const parsed = new URL(url);
    const pathname = parsed.pathname;
    const lastDotIndex = pathname.lastIndexOf(".");
    if (lastDotIndex === -1) return null;

    const ext = pathname.slice(lastDotIndex + 1).toLowerCase();
    return isValidImageExtension(ext) ? ext : null;
  } catch {
    return null;
  }
}

function mapStatus(upstreamStatus: number): number {
  // Avoid leaking upstream 5xx directly; treat as bad gateway.
  if (upstreamStatus >= 500) return 502;
  return upstreamStatus;
}

function createTimeoutAbortController(timeoutMs: number): {
  controller: AbortController;
  timeoutId: ReturnType<typeof setTimeout>;
} {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  return { controller, timeoutId };
}

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

function normalizeHeaders(
  headers: HeadersInit | undefined,
): Record<string, string> {
  if (!headers) return {};
  if (headers instanceof Headers) {
    return Object.fromEntries(headers.entries());
  }
  if (Array.isArray(headers)) {
    return Object.fromEntries(headers);
  }
  return headers;
}
