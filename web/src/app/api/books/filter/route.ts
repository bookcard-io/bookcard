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
 * POST /api/books/filter
 *
 * Proxies request to filter books from the active library.
 * Supports multiple filter criteria with OR conditions within each type.
 */
export async function POST(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const body = await request.json();
    const { searchParams } = request.nextUrl;
    const page = searchParams.get("page") || "1";
    const pageSize = searchParams.get("page_size") || "20";
    const sortBy = searchParams.get("sort_by") || "timestamp";
    const sortOrder = searchParams.get("sort_order") || "desc";

    const response = await client.request("/books/filter", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      queryParams: {
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder,
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to filter books" },
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
