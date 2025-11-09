import { type NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE_NAME, BACKEND_URL } from "@/constants/config";

/**
 * POST /api/books/filter
 *
 * Proxies request to filter books from the active library.
 * Supports multiple filter criteria with OR conditions within each type.
 */
export async function POST(request: NextRequest) {
  try {
    const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;

    if (!token) {
      return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const { searchParams } = request.nextUrl;
    const page = searchParams.get("page") || "1";
    const pageSize = searchParams.get("page_size") || "20";
    const sortBy = searchParams.get("sort_by") || "timestamp";
    const sortOrder = searchParams.get("sort_order") || "desc";

    const queryParams = new URLSearchParams({
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
    });

    const response = await fetch(
      `${BACKEND_URL}/books/filter?${queryParams.toString()}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      },
    );

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
