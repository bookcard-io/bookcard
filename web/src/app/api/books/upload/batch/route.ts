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
 * POST /api/books/upload/batch
 *
 * Proxy request to backend batch upload endpoint.
 */
export async function POST(request: NextRequest) {
  try {
    // Read formData first before any other request access
    const formData = await request.formData();

    // Get authenticated client after reading formData
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    // Create FormData for backend request
    const backendFormData = new FormData();
    const files = formData.getAll("files") as File[];
    for (const file of files) {
      backendFormData.append("files", file);
    }

    // Don't set Content-Type header for FormData - fetch will set it with boundary
    const response = await client.request("/books/upload/batch", {
      method: "POST",
      headers: {}, // Empty headers - fetch will set Content-Type for FormData
      body: backendFormData,
    });

    const responseText = await response.text();

    if (!response.ok) {
      let errorData: { detail?: string };
      try {
        errorData = JSON.parse(responseText) as { detail?: string };
      } catch {
        errorData = { detail: "Failed to upload books" };
      }
      return NextResponse.json(errorData, { status: response.status });
    }

    let data: unknown;
    try {
      data = JSON.parse(responseText);
    } catch {
      return NextResponse.json(
        { detail: "Invalid response from server" },
        { status: 500 },
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      {
        detail:
          error instanceof Error ? error.message : "Internal server error",
      },
      { status: 500 },
    );
  }
}
