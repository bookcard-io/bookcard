import { type NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE_NAME, BACKEND_URL } from "@/constants/config";

/**
 * GET /api/books/filter/suggestions
 *
 * Proxies request to the backend filter suggestions endpoint.
 */
export async function GET(request: NextRequest) {
  try {
    const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;

    if (!token) {
      return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    }

    const { searchParams } = request.nextUrl;
    const q = searchParams.get("q") || "";
    const filterType = searchParams.get("filter_type") || "";

    if (!q.trim() || !filterType.trim()) {
      return NextResponse.json({
        suggestions: [],
      });
    }

    const response = await fetch(
      `${BACKEND_URL}/books/filter/suggestions?q=${encodeURIComponent(q)}&filter_type=${encodeURIComponent(filterType)}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      },
    );

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
