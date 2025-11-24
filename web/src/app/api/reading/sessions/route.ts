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
 * POST /api/reading/sessions
 *
 * Proxies request to start a reading session.
 */
export async function POST(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const body = await request.json();

    const response = await client.request("/reading/sessions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to start reading session" },
        { status: response.status },
      );
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Error in POST /api/reading/sessions:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}

/**
 * GET /api/reading/sessions?book_id={book_id}&page={page}&page_size={page_size}
 *
 * Proxies request to list reading sessions.
 */
export async function GET(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { searchParams } = new URL(request.url);
    const bookId = searchParams.get("book_id");
    const page = searchParams.get("page");
    const pageSize = searchParams.get("page_size");

    const queryParams: Record<string, string> = {};
    if (bookId) {
      queryParams.book_id = bookId;
    }
    if (page) {
      queryParams.page = page;
    }
    if (pageSize) {
      queryParams.page_size = pageSize;
    }

    const response = await client.request("/reading/sessions", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      queryParams,
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to fetch reading sessions" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error in GET /api/reading/sessions:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
