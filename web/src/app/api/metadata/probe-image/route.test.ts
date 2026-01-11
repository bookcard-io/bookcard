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

import type { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

type ProbeMock = ReturnType<typeof vi.fn>;

/**
 * Create a minimal NextRequest-like object for API route testing.
 *
 * Parameters
 * ----------
 * url : string
 *     Full request URL.
 */
function createRequest(url: string): NextRequest {
  return {
    nextUrl: new URL(url),
  } as unknown as NextRequest;
}

describe("GET /api/metadata/probe-image", () => {
  let probeMock: ProbeMock;

  beforeEach(() => {
    vi.resetModules();
    probeMock = vi.fn();
    vi.spyOn(console, "warn").mockImplementation(() => {});

    vi.doMock("@/services/metadata/imageProbeService", () => ({
      ImageProbeService: class ImageProbeServiceMock {
        probe = probeMock;
      },
    }));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should return 400 when url param is missing", async () => {
    const { GET } = await import("./route");
    const res = await GET(
      createRequest("http://localhost/api/metadata/probe-image"),
    );

    expect(res.status).toBe(400);
    await expect(res.json()).resolves.toEqual({
      detail: "Missing url parameter",
    });
  });

  it("should return probed metadata on success", async () => {
    probeMock.mockResolvedValue({
      size: 123,
      mimeType: "image/jpeg",
      extension: "jpg",
    });

    const { GET } = await import("./route");
    const res = await GET(
      createRequest(
        "http://localhost/api/metadata/probe-image?url=https%3A%2F%2Fexample.com%2Fimage.jpg",
      ),
    );

    expect(res.status).toBe(200);
    await expect(res.json()).resolves.toEqual({
      size: 123,
      mimeType: "image/jpeg",
      extension: "jpg",
    });
  });

  it("should map ImageProbeError to its status code", async () => {
    const { GET } = await import("./route");
    const { ImageProbeError } = await import("@/types/imageProbe");
    probeMock.mockRejectedValue(new ImageProbeError("Forbidden URL", 400));
    const res = await GET(
      createRequest(
        "http://localhost/api/metadata/probe-image?url=http%3A%2F%2F127.0.0.1%2Fimage.jpg",
      ),
    );

    expect(res.status).toBe(400);
    await expect(res.json()).resolves.toEqual({ detail: "Forbidden URL" });
  });

  it("should treat TypeError as invalid URL", async () => {
    probeMock.mockRejectedValue(new TypeError("bad url"));

    const { GET } = await import("./route");
    const res = await GET(
      createRequest("http://localhost/api/metadata/probe-image?url=not-a-url"),
    );

    expect(res.status).toBe(400);
    await expect(res.json()).resolves.toEqual({ detail: "Invalid URL" });
  });

  it("should return 500 on unexpected errors", async () => {
    probeMock.mockRejectedValue(new Error("boom"));

    const { GET } = await import("./route");
    const res = await GET(
      createRequest(
        "http://localhost/api/metadata/probe-image?url=https%3A%2F%2Fexample.com%2Fimage.jpg",
      ),
    );

    expect(res.status).toBe(500);
    await expect(res.json()).resolves.toEqual({
      detail: "Failed to probe image",
    });
  });
});
