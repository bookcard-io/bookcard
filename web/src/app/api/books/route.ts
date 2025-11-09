import { type NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE_NAME, BACKEND_URL } from "@/constants/config";

/**
 * GET /api/books
 *
 * Proxies request to list books from the active library.
 * Supports pagination, search, and sorting.
 */
export async function GET(request: NextRequest) {
  try {
    const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;

    if (!token) {
      return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    }

    const { searchParams } = request.nextUrl;
    const page = searchParams.get("page") || "1";
    const pageSize = searchParams.get("page_size") || "20";
    const search = searchParams.get("search") || "";
    const sortBy = searchParams.get("sort_by") || "timestamp";
    const sortOrder = searchParams.get("sort_order") || "desc";

    const queryParams = new URLSearchParams({
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
    });

    if (search) {
      queryParams.append("search", search);
    }

    const response = await fetch(
      `${BACKEND_URL}/books?${queryParams.toString()}`,
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
        { detail: data.detail || "Failed to fetch books" },
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
