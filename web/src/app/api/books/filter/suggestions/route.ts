import { type NextRequest, NextResponse } from "next/server";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * GET /api/books/filter/suggestions
 *
 * Proxies request to the backend filter suggestions endpoint.
 */
export async function GET(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { searchParams } = request.nextUrl;
    const q = searchParams.get("q") || "";
    const filterType = searchParams.get("filter_type") || "";

    if (!q.trim() || !filterType.trim()) {
      return NextResponse.json({
        suggestions: [],
      });
    }

    const response = await client.request("/books/filter/suggestions", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      queryParams: {
        q,
        filter_type: filterType,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to fetch filter suggestions" },
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
