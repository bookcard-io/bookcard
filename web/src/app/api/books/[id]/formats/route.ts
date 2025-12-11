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
 * POST /api/books/[id]/formats
 *
 * Proxies request to add a new format to an existing book.
 * Handles file upload and optional replace parameter.
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    // Read formData first before any other request access
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
    const { searchParams } = request.nextUrl;
    const replace = searchParams.get("replace");

    // Create FormData for backend request
    const backendFormData = new FormData();
    backendFormData.append("file", file);

    const queryParams: Record<string, string> = {};
    if (replace === "true") {
      queryParams.replace = "true";
    }

    const response = await client.request(`/books/${id}/formats`, {
      method: "POST",
      headers: {}, // Let fetch set Content-Type with boundary
      body: backendFormData,
      queryParams,
    });

    const responseText = await response.text();

    if (!response.ok) {
      let errorData: { detail?: string };
      try {
        errorData = JSON.parse(responseText);
      } catch {
        errorData = { detail: "Failed to add format" };
      }
      return NextResponse.json(
        { detail: errorData.detail || "Failed to add format" },
        { status: response.status },
      );
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

    return NextResponse.json(data, { status: 201 });
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
