import { type NextRequest, NextResponse } from "next/server";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * GET /api/books/search/suggestions
 *
 * Proxies request to the backend search suggestions endpoint.
 */
export async function GET(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

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
