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
import {
  getAuthenticatedClient,
  getOptionalClient,
} from "@/services/http/routeHelpers";

/**
 * GET /api/books/[id]/cover
 *
 * Proxies request to get book cover image.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { client, error } = getOptionalClient(request);

    if (error) {
      return error;
    }

    const { id } = await params;

    const response = await client.request(`/books/${id}/cover`, {
      method: "GET",
    });

    if (!response.ok) {
      // If 404, just return 404
      if (response.status === 404) {
        return new NextResponse(null, { status: 404 });
      }

      const data = await response
        .json()
        .catch(() => ({ detail: "Failed to fetch cover" }));
      return NextResponse.json(
        { detail: data.detail || "Failed to fetch cover" },
        { status: response.status },
      );
    }

    // Get the file content
    const blob = await response.blob();
    const contentType = response.headers.get("content-type") || "image/jpeg";

    // Create response with file
    const fileResponse = new NextResponse(blob, {
      status: 200,
      headers: {
        "Content-Type": contentType,
        "Cache-Control": "public, max-age=86400, immutable", // Cache for 1 day
      },
    });

    return fileResponse;
  } catch (error) {
    console.error("Cover fetch error:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}

/**
 * POST /api/books/[id]/cover
 *
 * Proxies request to upload book cover image.
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    // Read formData first
    const formData = await request.formData();
    const file = formData.get("file") as File | null;

    if (!file) {
      return NextResponse.json({ detail: "No file provided" }, { status: 400 });
    }

    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { id } = await params;

    const backendFormData = new FormData();
    backendFormData.append("file", file);

    const response = await client.request(`/books/${id}/cover`, {
      method: "POST",
      headers: {}, // Empty headers - fetch will set Content-Type for FormData
      body: backendFormData,
    });

    if (!response.ok) {
      const data = await response
        .json()
        .catch(() => ({ detail: "Failed to upload cover" }));
      return NextResponse.json(
        { detail: data.detail || "Failed to upload cover" },
        { status: response.status },
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Cover upload error:", error);
    return NextResponse.json(
      {
        detail:
          error instanceof Error ? error.message : "Internal server error",
      },
      { status: 500 },
    );
  }
}
