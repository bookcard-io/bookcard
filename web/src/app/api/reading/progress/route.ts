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
 * PUT /api/reading/progress
 *
 * Proxies request to update reading progress.
 */
export async function PUT(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const body = await request.json();

    const response = await client.request("/reading/progress", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to update reading progress" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error in PUT /api/reading/progress:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}

/**
 * GET /api/reading/progress?book_id={book_id}&format={format}
 *
 * Proxies request to get reading progress for a book.
 */
export async function GET(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { searchParams } = new URL(request.url);
    const bookId = searchParams.get("book_id");
    const format = searchParams.get("format");

    if (!bookId || !format) {
      return NextResponse.json(
        { detail: "book_id and format are required" },
        { status: 400 },
      );
    }

    const response = await client.request(`/reading/progress/${bookId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      queryParams: {
        format,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to fetch reading progress" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error in GET /api/reading/progress:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
