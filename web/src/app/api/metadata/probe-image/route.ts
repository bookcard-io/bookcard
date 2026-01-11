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

import { type NextRequest, NextResponse } from "next/server";
import { ImageProbeService } from "@/services/metadata/imageProbeService";
import { ImageProbeError, InvalidUrlError } from "@/types/imageProbe";

export const runtime = "nodejs";

const imageProbeService = new ImageProbeService({
  config: {
    followRedirects: false,
    timeoutMs: 10_000,
    maxSizeBytes: 50 * 1024 * 1024,
  },
});

/**
 * GET /api/metadata/probe-image
 *
 * Probes an external image URL for its size (Content-Length),
 * MIME type, and inferred extension.
 * Used to bypass CORS restrictions on the client side.
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const url = searchParams.get("url");

    if (!url) {
      return jsonError("Missing url parameter", 400);
    }

    const result = await imageProbeService.probe(url);
    return NextResponse.json(result);
  } catch (error) {
    if (error instanceof ImageProbeError) {
      return jsonError(error.message, error.statusCode);
    }

    // URL parsing can throw TypeError depending on runtime.
    if (error instanceof TypeError) {
      const invalid = new InvalidUrlError("Invalid URL", error);
      return jsonError(invalid.message, invalid.statusCode);
    }

    console.warn("Image probe error:", error);
    return jsonError("Failed to probe image", 500);
  }
}

function jsonError(detail: string, status: number) {
  return NextResponse.json({ detail }, { status });
}
