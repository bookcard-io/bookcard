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

import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  NotImageError,
  SSRFError,
  TooLargeError,
  UpstreamError,
} from "@/types/imageProbe";

vi.mock("@/utils/security/ssrf", () => ({
  validateRemoteHttpUrl: vi.fn(),
}));

import { validateRemoteHttpUrl } from "@/utils/security/ssrf";
import { ImageProbeService } from "./imageProbeService";

type FetchLike = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;
type FetchMock = ReturnType<typeof vi.fn<FetchLike>>;
type ServiceConfig = Partial<
  NonNullable<ConstructorParameters<typeof ImageProbeService>[0]>["config"]
>;

/**
 * Create a Response with headers for probing.
 *
 * Parameters
 * ----------
 * params : object
 *     Response parameters.
 */
function createProbeResponse(params: {
  status: number;
  headers?: Record<string, string>;
}): Response {
  return new Response("", {
    status: params.status,
    headers: params.headers,
  });
}

/**
 * Create a service with a mocked fetch implementation.
 *
 * Parameters
 * ----------
 * fetchImpl : FetchMock
 *     Mock fetch function.
 * config : object, optional
 *     Config overrides.
 */
function createService(fetchImpl: FetchMock, config?: ServiceConfig) {
  return new ImageProbeService({
    fetchImpl,
    config,
  });
}

describe("ImageProbeService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(validateRemoteHttpUrl).mockImplementation(
      async (rawUrl: string) => {
        return new URL(rawUrl);
      },
    );
  });

  it("should call HEAD and return metadata when HEAD succeeds", async () => {
    const mockFetch = vi.fn<FetchLike>().mockResolvedValue(
      createProbeResponse({
        status: 200,
        headers: {
          "content-length": "123",
          "content-type": "image/jpeg; charset=utf-8",
        },
      }),
    );

    const service = createService(mockFetch);
    const result = await service.probe("https://example.com/image.jpg");

    expect(result).toEqual({
      size: 123,
      mimeType: "image/jpeg",
      extension: "jpg",
    });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(URL),
      expect.objectContaining({
        method: "HEAD",
        redirect: "manual",
        headers: expect.objectContaining({
          "User-Agent": "BookCard/1.0",
        }),
      }),
    );
  });

  it("should fallback to Range GET when HEAD fails", async () => {
    const mockFetch = vi
      .fn<FetchLike>()
      .mockResolvedValueOnce(createProbeResponse({ status: 405 }))
      .mockResolvedValueOnce(
        createProbeResponse({
          status: 200,
          headers: {
            "content-range": "bytes 0-0/2048",
            "content-type": "image/png",
          },
        }),
      );

    const service = createService(mockFetch);
    const result = await service.probe("https://example.com/image.png");

    expect(result).toEqual({
      size: 2048,
      mimeType: "image/png",
      extension: "png",
    });

    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(mockFetch.mock.calls[0]?.[1]).toEqual(
      expect.objectContaining({ method: "HEAD" }),
    );
    expect(mockFetch.mock.calls[1]?.[1]).toEqual(
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({
          Range: "bytes=0-0",
          "User-Agent": "BookCard/1.0",
        }),
      }),
    );
  });

  it("should reject redirects when followRedirects is false", async () => {
    const mockFetch = vi.fn<FetchLike>().mockResolvedValue(
      createProbeResponse({
        status: 302,
        headers: {
          location: "https://internal.local/secret",
        },
      }),
    );

    const service = createService(mockFetch, { followRedirects: false });
    const promise = service.probe("https://example.com/redirect");
    await expect(promise).rejects.toBeInstanceOf(UpstreamError);
    await expect(promise).rejects.toEqual(
      expect.objectContaining({ statusCode: 400 }),
    );
  });

  it("should throw NotImageError when content-type is not an image", async () => {
    const mockFetch = vi.fn<FetchLike>().mockResolvedValue(
      createProbeResponse({
        status: 200,
        headers: {
          "content-type": "text/html; charset=utf-8",
        },
      }),
    );

    const service = createService(mockFetch);
    await expect(
      service.probe("https://example.com/index.html"),
    ).rejects.toBeInstanceOf(NotImageError);
  });

  it("should throw TooLargeError when size exceeds maxSizeBytes", async () => {
    const mockFetch = vi.fn<FetchLike>().mockResolvedValue(
      createProbeResponse({
        status: 200,
        headers: {
          "content-length": String(51 * 1024 * 1024),
          "content-type": "image/jpeg",
        },
      }),
    );

    const service = createService(mockFetch, {
      maxSizeBytes: 50 * 1024 * 1024,
    });
    await expect(
      service.probe("https://example.com/huge.jpg"),
    ).rejects.toBeInstanceOf(TooLargeError);
  });

  it("should map AbortError to UpstreamError 504", async () => {
    const abort = Object.assign(new Error("aborted"), { name: "AbortError" });
    const mockFetch = vi.fn<FetchLike>().mockRejectedValue(abort);

    const service = createService(mockFetch, { timeoutMs: 1 });
    await expect(
      service.probe("https://example.com/image.jpg"),
    ).rejects.toEqual(
      expect.objectContaining({
        name: "UpstreamError",
        statusCode: 504,
      }),
    );
  });

  it("should preserve SSRF errors from validator", async () => {
    vi.mocked(validateRemoteHttpUrl).mockRejectedValue(
      new SSRFError("Forbidden URL"),
    );

    const mockFetch = vi.fn<FetchLike>();
    const service = createService(mockFetch);

    await expect(
      service.probe("http://127.0.0.1/image.jpg"),
    ).rejects.toBeInstanceOf(SSRFError);
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("should infer extension from URL when mime is unknown but still image/*", async () => {
    const mockFetch = vi.fn<FetchLike>().mockResolvedValue(
      createProbeResponse({
        status: 200,
        headers: {
          "content-type": "image/unknown",
        },
      }),
    );

    const service = createService(mockFetch);
    const result = await service.probe("https://example.com/picture.webp");

    expect(result.extension).toBe("webp");
    expect(result.mimeType).toBe("image/unknown");
  });
});
