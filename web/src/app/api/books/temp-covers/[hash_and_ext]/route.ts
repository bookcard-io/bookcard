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
 * GET /api/books/temp-covers/[hash_and_ext]
 *
 * Proxies request to get temporary cover image.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ hash_and_ext: string }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { hash_and_ext } = await params;

    const response = await client.request(
      `/books/temp-covers/${hash_and_ext}`,
      {
        method: "GET",
      },
    );

    if (!response.ok) {
      return NextResponse.json(
        { detail: "Failed to fetch temporary cover" },
        { status: response.status },
      );
    }

    // Return the image file
    const imageBuffer = await response.arrayBuffer();
    return new NextResponse(imageBuffer, {
      headers: {
        "Content-Type": response.headers.get("Content-Type") || "image/jpeg",
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
