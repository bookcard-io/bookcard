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
import type { BookUpdate } from "@/types/book";

/**
 * POST /api/books/metadata/import
 *
 * Proxies request to import metadata from file (OPF or YAML) to the backend.
 */
export async function POST(request: NextRequest) {
  try {
    // Read formData first before any other request access
    // to avoid "body already consumed" errors in Next.js
    const formData = await request.formData();
    const file = formData.get("file") as File | null;

    if (!file) {
      return NextResponse.json({ detail: "No file provided" }, { status: 400 });
    }

    // Get authenticated client after reading formData
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    // Create FormData for backend request
    const backendFormData = new FormData();
    backendFormData.append("file", file);

    // Don't set Content-Type header for FormData - fetch will set it with boundary
    const response = await client.request("/books/metadata/import", {
      method: "POST",
      headers: {}, // Empty headers - fetch will set Content-Type for FormData
      body: backendFormData,
    });

    // Read response body as text first, then parse JSON manually
    const responseText = await response.text();

    if (!response.ok) {
      let errorData: { detail?: string };
      try {
        errorData = JSON.parse(responseText) as { detail?: string };
      } catch {
        errorData = { detail: "Failed to import metadata" };
      }
      return NextResponse.json(
        { detail: errorData.detail || "Failed to import metadata" },
        { status: response.status },
      );
    }

    let data: BookUpdate;
    try {
      data = JSON.parse(responseText) as BookUpdate;
    } catch {
      return NextResponse.json(
        { detail: "Invalid response from server" },
        { status: 500 },
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error("Metadata import error:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
