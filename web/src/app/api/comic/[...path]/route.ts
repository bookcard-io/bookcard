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
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * GET /api/comic/[...path]
 *
 * Proxies request to backend comic endpoints.
 * Handles both JSON (page list) and image (page content) responses.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { path } = await params;
    const backendPath = `/comic/${path.join("/")}`;
    const searchParams = request.nextUrl.searchParams;
    const queryString = searchParams.toString();
    const url = queryString ? `${backendPath}?${queryString}` : backendPath;

    const response = await client.request(url, {
      method: "GET",
      // Forward necessary headers if needed, but client handles auth
    });

    if (!response.ok) {
      // Try to parse JSON error if possible
      try {
        const errorData = await response.json();
        console.error(`Comic backend error (${response.status}):`, errorData);
        return NextResponse.json(errorData, { status: response.status });
      } catch {
        // Fallback for non-JSON errors
        console.error(
          `Comic backend error (${response.status}): Non-JSON response`,
        );
        return new NextResponse(response.body, { status: response.status });
      }
    }

    // Stream the response body directly to support both JSON and images
    // Forward Content-Type and Cache-Control headers
    const headers = new Headers();
    const contentType = response.headers.get("Content-Type");
    const cacheControl = response.headers.get("Cache-Control");
    const contentLength = response.headers.get("Content-Length");

    if (contentType) headers.set("Content-Type", contentType);
    if (cacheControl) headers.set("Cache-Control", cacheControl);
    if (contentLength) headers.set("Content-Length", contentLength);

    return new NextResponse(response.body, {
      status: 200,
      headers,
    });
  } catch (error) {
    console.error("Comic proxy error:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
