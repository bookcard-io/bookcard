import { type NextRequest, NextResponse } from "next/server";
import { getOptionalClient } from "@/services/http/routeHelpers";

/**
 * GET /api/libraries/active
 *
 * Proxies request to get the active library.
 *
 * This endpoint supports anonymous access when anonymous browsing is enabled
 * on the backend.
 */
export async function GET(request: NextRequest) {
  try {
    const { client, error } = getOptionalClient(request);

    if (error) {
      return error;
    }

    const response = await client.request("/libraries/active", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to fetch active library" },
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
