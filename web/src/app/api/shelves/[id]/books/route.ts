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
 * GET /api/shelves/[id]/books
 *
 * Proxies request to get books in a shelf.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { id } = await params;
    const { searchParams } = request.nextUrl;
    const page = searchParams.get("page") || "1";
    const pageSize = searchParams.get("page_size") || "20";
    const sortBy = searchParams.get("sort_by") || "order";
    const sortOrder = searchParams.get("sort_order") || "asc";

    const queryParams: Record<string, string> = {
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
    };

    const response = await client.request(`/shelves/${id}/books`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      queryParams,
    });

    const data = await (async () => {
      try {
        return (await response.json()) as unknown;
      } catch {
        const text = await response.text().catch(() => "");
        return { detail: text || "Failed to fetch shelf books" };
      }
    })();

    if (!response.ok) {
      const detail =
        typeof data === "object" && data !== null && "detail" in data
          ? (data as { detail?: string }).detail
          : undefined;
      return NextResponse.json(
        { detail: detail || "Failed to fetch shelf books" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error in GET /api/shelves/[id]/books:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
