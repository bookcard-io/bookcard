import { type NextRequest, NextResponse } from "next/server";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * GET /api/fs/suggest_dirs
 *
 * Proxies request to the backend directory suggestions endpoint.
 */
export async function GET(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const { searchParams } = request.nextUrl;
    const q = searchParams.get("q") || "";
    const limit = searchParams.get("limit") || "50";

    const response = await client.request("/fs/suggest_dirs", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      queryParams: {
        q,
        limit,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to fetch directory suggestions" },
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
