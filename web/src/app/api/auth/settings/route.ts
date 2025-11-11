import { type NextRequest, NextResponse } from "next/server";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * GET /api/auth/settings
 *
 * Proxies request to get all user settings.
 */
export async function GET(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const response = await client.request("/auth/settings", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to fetch settings" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error in GET /api/auth/settings:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
