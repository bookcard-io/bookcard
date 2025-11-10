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
