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
import { getOptionalClient } from "@/services/http/routeHelpers";

/**
 * GET /api/books/search/suggestions
 *
 * Proxies request to the backend search suggestions endpoint.
 */
export async function GET(request: NextRequest) {
  try {
    const { client, error } = getOptionalClient(request);

    if (error) {
      return error;
    }

    const { searchParams } = request.nextUrl;
    const q = searchParams.get("q") || "";

    if (!q.trim()) {
      return NextResponse.json({
        books: [],
        authors: [],
        tags: [],
        series: [],
      });
    }

    const response = await client.request("/books/search/suggestions", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      queryParams: {
        q,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to fetch search suggestions" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
