import { type NextRequest, NextResponse } from "next/server";
import { getOptionalClient } from "@/services/http/routeHelpers";

/**
 * GET /api/config/anonymous-browsing
 *
 * Public endpoint to read the anonymous browsing setting.
 */
export async function GET(request: NextRequest) {
  try {
    const { client, error } = getOptionalClient(request);

    if (error) {
      return error;
    }

    const response = await client.request("/admin/basic-config/public", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to fetch config" },
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
